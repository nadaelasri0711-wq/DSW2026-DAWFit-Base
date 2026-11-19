 from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required
from app.models import db, Actividad

public_bp = Blueprint("public", __name__)
busqueda = request.args.get("busqueda", "").strip()
solo_con_plazas = request.args.get("solo_con_plazas")




@public_bp.route("/")
def home():
    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/actividades")
def mostrar_actividades():

    actividades = Actividad.query.all()

    deporte_fav = None

    return render_template(
        "catalogo.html",
        lista_actividades=actividades,
        deporte_fav=deporte_fav,
    )


@public_bp.route("/actividad/<int:act_id>")
def ver_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    return render_template("actividad_detalle.html", actividad=actividad)


@public_bp.route("/preferencia/<string:deporte>")
def guardar_preferencia(deporte):
    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/limpiar-preferencia")
def limpiar_preferencia():
    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/reservas/apuntar/<int:act_id>", methods=["POST"])
@login_required
def apuntar_actividad(act_id):
    flash("Funcionalidad de inscripción pendiente de implementar.", "info")
    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/reservas")
@login_required
def ver_reservas():
    return render_template(
        "reservas.html",
        actividades=[],
        total_sin_descuento=0.0,
        descuento_aplicado=False,
        total_final=0.0,
    )
    
#Cancelación

@public_bp.route("/reservas/cancelar/<int:act_id>", methods=["POST"])
@login_required
def cancelar_reserva(act_id):
    reservas = session.get("reservas", [])

    if act_id in reservas:
        session["reservas"].remove(act_id)
        session.modified = True
        flash("Has quitado la actividad de tus reservas.", "info")
    else:
        flash("Esa actividad no estaba en tus reservas.", "error")

    return redirect(url_for("public.ver_reservas"))


# Confirmar

@public_bp.route("/reservas/confirmar", methods=["POST"])
@login_required
def confirmar_reservas():
    ids_reservas = session.get("reservas", [])

    if not ids_reservas:
        flash("No tienes reservas pendientes que confirmar.", "info")
        return redirect(url_for("public.mostrar_actividades"))

    actividades = Actividad.query.filter(Actividad.id.in_(ids_reservas)).all()
    for act in actividades:
        act.plazas_libres -= 1
    db.session.commit()

    session.pop("reservas", None)
    flash("¡Inscripciones confirmadas! Se han descontado las plazas.", "exito")
    return redirect(url_for("public.mostrar_actividades"))

#Verifica tres reglas antes de añadir el identificador: que plazas_libres > 0, que el
#identificador no esté ya dentro de session["reservas"] y que la lista tenga menos de 3
#actividades

@public_bp.route("/reservas/apuntar/<int:act_id>", methods=["POST"])
@login_required
def apuntar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    session.permanent = True
    reservas = session.get("reservas", [])

#Si incumple alguna regla, muestra un aviso flash() de categoría "error" explicando el
#motivo sin modificar la lista
    if actividad.plazas_libres <= 0:
        flash(f"'{actividad.nombre}' tiene el cupo lleno.", "error")
    elif act_id in reservas:
        flash(f"Ya estás apuntado a '{actividad.nombre}'.", "error")
    elif len(reservas) >= 3:
        flash("Solo puedes tener 3 actividades reservadas a la vez.", "error")
    else:
        if "reservas" not in session:
            session["reservas"] = []
        session["reservas"].append(act_id)
        session.modified = True
        flash(f"Te has apuntado a '{actividad.nombre}'.", "exito")

    return redirect(url_for("public.mostrar_actividades"))

#Si cumple las tres, añade el identificador a session["reservas"], marca session.modified =
#True y lanza un aviso de éxito

@public_bp.route("/reservas")
@login_required
def ver_reservas():
    ids_reservas = session.get("reservas", [])

    if ids_reservas:
        actividades = Actividad.query.filter(Actividad.id.in_(ids_reservas)).all()
    else:
        actividades = []

    total_sin_descuento = sum(act.cuota for act in actividades)

    descuento_aplicado = len(ids_reservas) == 3
    if descuento_aplicado:
        total_final = total_sin_descuento * 0.80
    else:
        total_final = total_sin_descuento

    return render_template(
        "reservas.html",
        actividades=actividades,
        total_sin_descuento=total_sin_descuento,
        descuento_aplicado=descuento_aplicado,
        total_final=total_final,
    )
    
     