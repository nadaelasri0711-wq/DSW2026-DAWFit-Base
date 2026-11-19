import os
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.models import db, login_manager, Actividad
from app.forms import ActividadForm


#función con @admin_bp.before_request que redirija al login si el
#usuario es anónimo (login_manager.unauthorized()) y lance abort(403) si no cumple
#current_user.es_monitor
 admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
@admin_bp.before_request
def verificar_permisos():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    if not current_user.es_monitor:
        abort(403) 

@admin_bp.route("/actividad/nueva", methods=["GET", "POST"])
def crear_actividad():
    form = ActividadForm()
    return render_template(
        "actividad_form.html", form=form, titulo="Nueva Actividad Deportiva"
    )


@admin_bp.route("/actividad/<int:act_id>/editar", methods=["GET", "POST"])
def editar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    form = ActividadForm(obj=actividad)

    return render_template(
        "actividad_form.html",
        form=form,
        titulo="Editar Actividad",
        actividad=actividad,
    )


@admin_bp.route("/actividad/<int:act_id>/eliminar", methods=["POST"])
def eliminar_actividad(act_id):
    flash("Eliminación pendiente de implementar.", "info")
    return redirect(url_for("public.mostrar_actividades"))

#Si el monitor sube una imagen, limpia su nombre con secure_filename() y antepón el
#deporte en minúsculas seguido de guion bajo:
#<deporte_en_minusculas>_<nombre_seguro> (ej. padel_cartel.jpg).

def guardar_cartel(archivo, deporte):
    nombre_seguro = secure_filename(archivo.filename)
    nombre_final = f"{secure_filename(deporte.lower())}_{nombre_seguro}"

#Guarda el archivo físico en el directorio configurado en UPLOAD_FOLDER y almacena el
#nombre resultante en la base de datos.
    carpeta_subidas = current_app.config["UPLOAD_FOLDER"]
    
#Al editar una actividad, permite guardar cambios aunque mantenga su propio nombre
#original y, si se sube un cartel nuevo distinto al anterior, borra del disco duro la imagen
#antigua con os.remove()
    os.makedirs(carpeta_subidas, exist_ok=True)
    archivo.save(os.path.join(carpeta_subidas, nombre_final))
    return nombre_final

#Crear
if form.validate_on_submit():
    nombre_imagen = None
    if form.archivo_imagen.data:
        nombre_imagen = guardar_cartel(form.archivo_imagen.data, form.deporte.data)

    nueva_actividad = Actividad(
        nombre=form.nombre.data, deporte=form.deporte.data,
        cuota=form.cuota.data, plazas_libres=form.plazas_libres.data,
        imagen=nombre_imagen,
    )
    db.session.add(nueva_actividad)
    db.session.commit()
    flash("Actividad creada correctamente.", "exito")
    return redirect(url_for("public.mostrar_actividades"))

actividad = db.get_or_404(Actividad, act_id)
form = ActividadForm(obj=actividad, actividad_id=actividad.id)

#Editar
if form.validate_on_submit():
    actividad.nombre = form.nombre.data
    actividad.deporte = form.deporte.data
    actividad.cuota = form.cuota.data
    actividad.plazas_libres = form.plazas_libres.data

    if form.archivo_imagen.data:
        nombre_imagen = guardar_cartel(form.archivo_imagen.data, form.deporte.data)
        if actividad.imagen and actividad.imagen != nombre_imagen:
            ruta_antigua = os.path.join(current_app.config["UPLOAD_FOLDER"], actividad.imagen)
            if os.path.exists(ruta_antigua):
                os.remove(ruta_antigua)
        actividad.imagen = nombre_imagen

    db.session.commit()
    flash("Actividad actualizada con éxito.", "exito")
    return redirect(url_for("public.mostrar_actividades"))


#Si la actividad tiene el cupo lleno (plazas_libres == 0), impide su borrado, lanza un
#mensaje flash() con categoría "error" y redirige al catálogo
actividad = db.get_or_404(Actividad, act_id)
nombre = actividad.nombre

if actividad.plazas_libres == 0:
    flash(f"No se puede eliminar '{nombre}': el cupo está lleno.", "error")
    return redirect(url_for("public.mostrar_actividades"))

#Si tiene plazas_libres > 0, elimina primero su archivo de imagen del disco duro (si tiene
#uno y existe en la carpeta de subidas) y después borra el registro de la base de datos.
if actividad.imagen:
    ruta_imagen = os.path.join(current_app.config["UPLOAD_FOLDER"], actividad.imagen)
    if os.path.exists(ruta_imagen):
        os.remove(ruta_imagen)

db.session.delete(actividad)
db.session.commit()
flash(f"Actividad '{nombre}' eliminada.", "exito")
return redirect(url_for("public.mostrar_actividades"))
