from datetime import datetime
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import jwt
from dateutil import tz
from functools import wraps
import psycopg2
import hashlib
app = Flask(__name__)
app.config['SECRET_KEY'] = '3643dcdf2beb1ace0f0dd02019e9bee9'
CORS(app, support_credentials=True)


'#-----------------------------------------------------Conexion Base de Datos-----------------------------------------'


def connectdb():
    user = 'postgres'
    password = 'postgres'
    dbname = 'plasticos'
    host = '127.0.0.1'
    try:
        action = f"dbname='{dbname}' user='{user}'host='{host}' password='{password}'"
        conn = psycopg2.connect(action)
        return conn
    except Exception as e:
        print(str(e))
        exit()
        return False


'#-------------------------------------------------Funciones--------------------------------------------------------'


def validateJson(inputIn, field):
    print('Se valida el campo -> ' + field)
    if inputIn and field in inputIn:
        print(inputIn[field])
        print(type(inputIn[field]))
        if inputIn[field] == '':
            return False
        else:
            if type(inputIn[field]) == bool:
                print('El campo es un booleano')
                return str(inputIn[field])
            if type(inputIn[field]) == list:
                print('El campo es una lista')
                return inputIn[field]
            if type(inputIn[field]) == str:
                print('El campo es un string')
                return inputIn[field]
            if type(inputIn[field]) == int:
                print('El campo es un numero')
                return inputIn[field]
            else:
                return inputIn[field]
    else:
        return False

def getInput(inputIn):
    if inputIn == False:
        return False
    else:
        return str(inputIn)


def nowWithTzDate():
    utc_dt = datetime.datetime.now()
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Mexico_City')
    utc = utc_dt.replace(tzinfo=from_zone)
    mexTime = utc.astimezone(to_zone)
    return mexTime


'#------------------------------------------------------JWT----------------------------------------------------------'


def token_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')

        if not token:
            return jsonify({'message': 'No se proporciono token', 'response': False, 'token_success': False}), 400

        else:
            try:
                data = jwt.decode(token, app.config['SECRET_KEY'])
                print(data)
                print(type(data))

            except Exception as e:
                print(e)
                return jsonify({'message': 'El token es invalido', 'response': False, 'token_success': False}), 401

            return f(*args, **kwargs)

    return decorated


'#--------------------------------------------Servicio Raiz-----------------------------------------------------------'


@app.route("/", methods=['POST', 'GET'])
def principal_metodo():
    return "Servicio Raiz"


'#------------------------------------------------------Login----------------------------------------------------------'


@app.route('/login', methods=['POST'])
@cross_origin(supports_credentials=True)
def login():
    print('login')
    output = {'response': False}

    inputIn = request.get_json(silent=True)

    print('Se valida JSON de entrada')
    print(inputIn)
    if inputIn is not None:
        print('Hay un JSON de entrada')
        # Email
        email = getInput(validateJson(inputIn, 'email')).lower()
        if email == False:
            output['email'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

        # Contraseña
        password = getInput(validateJson(inputIn, 'password'))
        if password == False:
            output['password'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

    else:
        print('No se proporciono JSON')
        output['body'] = 'No se proporciono body'
        return jsonify(output), 400

    con = connectdb()
    if con == False:
        output['message'] = 'No se puede conectar a la BD'
        return jsonify(output), 401

    cur = con.cursor()
    try:
        print('Se obtiene la informacion de inicio de sesion del usuario')
        query = f"select * from usuario where email = '{str(email)}'"
        print(query)
        cur.execute(query)
        usuarioEmail = cur.fetchone()
        if usuarioEmail is None:
            print('No se encontro una cuenta registrada con el correo electronico proporcionado')
            output['message'] = 'No se encontro una cuenta registrada con el correo electronico proporcionado'
            return jsonify(output), 401

        else:
            print('Se encontro una cuenta registrada, verificar contraseña')

            passwordBD = str(usuarioEmail[4])
            user = str(usuarioEmail[3])
            nombres =  str(usuarioEmail[1])
            apellidos = str(usuarioEmail[2])
            if passwordBD != password:
                print('La contraseña es incorrecta')
                output['message'] = 'La contraseña es incorrecta'
                return jsonify(output), 401
            else:

                print('La contraseña es correcta')
                expDate = nowWithTzDate() + datetime.timedelta(minutes=1300)
                print(f'El token expirara el {expDate}')
                token = jwt.encode({'user': email, 'exp': expDate},
                                           app.config['SECRET_KEY'])
                output['token'] = token.decode('UTF-8')

    except Exception as e:
        print(e)
        print('Ocurrio un error al verificar al usuario en la BD')
        output['message'] = 'Ocurrio un error al verificar al usuario en la BD'
        return jsonify(output), 500

    output["Usuario"] = user
    output["Nombre"] = nombres
    output["apellido"] = apellidos
    output['message'] = 'Se inicio sesion correctamente'
    output['response'] = True

    con.commit()
    cur.close()
    con.close()
    print('Ejecucion correcta')
    return jsonify(output), 200


'#---------------------------------------------------Crear Usuario----------------------------------------------------'


@app.route('/login/adduser', methods=['POST'])
@token_user
@cross_origin(supports_credentials=True)
def adduser():
    print('adduser')
    json_out = {}
    json_out["response"] = False
    output = {'response': False}

    inputIn = request.get_json(silent=True)

    print('Se valida JSON de entrada')
    print(inputIn)
    if inputIn is not None:
        print('Hay un JSON de entrada')
        # Nombres
        nombres = getInput(validateJson(inputIn, 'nombres')).lower()
        if nombres == False:
            output['nombres'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

        # Apellidos
        apellidos = getInput(validateJson(inputIn, 'apellidos'))
        if apellidos == False:
            output['apellidos'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

        # Email
        email = getInput(validateJson(inputIn, 'email'))
        if email == False:
            output['email'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

        # Password
        if request.json is None:
            json_out["error"] = "No se envio body en la solicitud"
            return json_out, 400
        else:
            content = request.json
            pass

        if 'password' in content:
            print("pasa password")
            password = content["password"]
            pass
        else:
            json_out["error"] = "No se envio el password"
            return json_out, 500

        hash_object = hashlib.md5(password.encode())
        md5_hash = hash_object.hexdigest()
        print('Clave Encriptada', md5_hash)

        # Tipo
        tipo = getInput(validateJson(inputIn, 'tipo'))
        if tipo == False:
            output['tipo'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

        # Telefono
        telefono = getInput(validateJson(inputIn, 'telefono'))
        if tipo == False:
            output['telefono'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

        # Descripcion
        descripcion = getInput(validateJson(inputIn, 'descripcion'))
        if tipo == False:
            output['descripcion'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

    else:
        print('No se proporciono JSON')
        output['body'] = 'No se proporciono body'
        return jsonify(output), 400

    con = connectdb()
    if con == False:
        output['message'] = 'No se puede conectar a la BD'
        return jsonify(output), 401

    cur = con.cursor()
    try:

        print('Se obtiene la informacion propocionada para validar no exista la cuenta')
        query = f"select * from usuario where email = '{str(email)}'"
        print(query)
        cur.execute(query)
        usuarioEmail = cur.fetchone()
        if usuarioEmail is not None:
            print('ERROR se encontro una cuenta registrada con el correo electronico proporcionado')
            output['message'] = 'ERROR se encontro una cuenta registrada con el correo electronico proporcionado'
            return jsonify(output), 401

        else:
            print('No se encontro una cuenta registrada con email, validar telefono')
            query = f"select * from usuario where telefono = '{str(telefono)}'"
            print(query)
            cur.execute(query)
            usuarioTelefono = cur.fetchone()

            if usuarioTelefono is not None:
                print(' ERROR se encontro una cuenta registrada con el telefono proporcionado')
                output['message'] = 'ERROR Se encontro una cuenta registrada con el telefono proporcionado'
                return jsonify(output), 401

            else:
                print('No se encontro el telefono en la BD, se procede a crear cuenta')
                fecha_hoy = datetime.datetime.today().strftime('%Y-%m-%d %H:%M')
                print('Se hace insert a la tabla usuario para crear el usuario')
                cur = con.cursor()
                query = f"insert into usuario values (default, '{nombres}', '{apellidos}', '{email}'," \
                        f"'{md5_hash}', '{tipo}', '{telefono}', '{descripcion}', false, '{fecha_hoy}')"
                print(query)
                cur.execute(query)

    except Exception as e:
        print(e)
        print('Ocurrio un error al crear al usuario en la BD')
        output['message'] = 'Ocurrio un error al crear al usuario en la BD'
        return jsonify(output), 500

    output['message'] = 'Se creo el usuario exitosamente'
    output['response'] = True

    con.commit()
    cur.close()
    con.close()
    print('Ejecucion correcta')
    return jsonify(output), 200


'#-----------------------------------------------Obtener Usuario-----------------------------------------------------'


@app.route("/login/getuser/<idusuario>", methods=['GET'])
@token_user
@cross_origin(supports_credentials=True)
def getusuerinfo(idusuario):

    global id, nombres, apellidos, email, tipo, telefono, descripcion, creacion
    print('getusuerinfo')
    output = {'response': False}
    con = connectdb()
    cur = con.cursor()

    try:
        print('Se hace select a la base de datos para obtener la info del usuario')
        query = f"select * from usuario where id = {idusuario} and eliminado = false"
        print(query)
        cur.execute(query)
        usuario = cur.fetchone()
        print(usuario)

        if usuario is None:

            print(' Error no se encontro la informacion del usuario')
            output['message'] = 'Error no se encontro la informacion del usuario'
            return jsonify(output), 401

        else:
            print('Se encontro la informacion del usuario')
            id = usuario[0]
            nombres = usuario[1]
            apellidos = usuario[2]
            email = usuario[3]
            tipo = usuario[5]
            telefono = usuario[6]
            descripcion = usuario[7]
            creacion = usuario[9].strftime('%d-%m-%Y %H:%M')

    except Exception as e:
        print(e)
        print('Ocurrio un error al buscar el usuario en la BD')
        output['message'] = 'Ocurrio un error al buscar el usuario en la BD'
        return jsonify(output), 500

    output["id"] = id
    output["nombres"] = nombres
    output["apellidos"] = apellidos
    output["email"] = email
    output["tipo"] = tipo
    output["telefono"] = telefono
    output["descripcion"] = descripcion
    output["creacion"] = creacion
    output['message'] = 'Datos encontrados exitosamente'
    output['response'] = True
    con.commit()
    cur.close()
    con.close()
    print('Ejecucion correcta')

    return jsonify(output), 200


'#----------------------------------------Obtener todos los usuarios-----------------------------------------------'


@app.route("/login/getusers", methods=['GET'])
@token_user
@cross_origin(supports_credentials=True)
def getusers():

    print('getusers')
    output = {'response': False}
    usuariosarray = []

    con = connectdb()
    if con == False:
        output['message'] = 'No se puede conectar a la BD'
        return jsonify(output), 401

    cur = con.cursor()

    try:

        print('Se realiza consulta a la base para buscar los usuarios creados')
        query = f"select * from usuario where eliminado = false order by fecha_creacion DESC"
        print(query)
        cur.execute(query)
        usuarios = cur.fetchall()
        print(usuarios)

        if usuarios is None or usuarios == []:
            print('No se encontraron usuarios')

        else:
            print('Se encontraron los usuarios  iterar en ellos')
            j = 0
            for i in usuarios:
                j = j+1
                print('Usuario creado #', str(j)+':', i)
                id = i[0]
                nombres = i[1]
                apellidos = i[2]
                email = i[3]
                tipo = i[5]
                telefono = i[6]
                descripcion = i[7]
                fechacreacion = i[9].strftime('%Y-%m-%d %H:%M')

                iObj = {

                    'id': id,
                    'nombres': nombres,
                    'apellidos': apellidos,
                    'email': email,
                    'tipo': tipo,
                    'telefono': telefono,
                    'descripcion': descripcion,
                    'fechacreacion': fechacreacion,

                }
                usuariosarray.append(iObj)
            else:
                print('Se obtuvieron los usuarios registrados')

        output['Usuarios'] = usuariosarray

    except Exception as e:
        print(e)
        print('Ocurrio un error al obtener los usuarios')
        output['message'] = 'Ocurrio un error al obtener los usuarios '
        return jsonify(output), 500

    output['message'] = 'Se obtuvieron correctamente los usuarios registrados '
    output['response'] = True
    con.commit()
    cur.close()
    con.close()
    print('Ejecucion correcta')
    return jsonify(output), 200


'#---------------------------------------------Update usuario-------------------------------------------------------'


@app.route("/login/edituser", methods=['POST'])
@token_user
@cross_origin(supports_credentials=True)
def edituser():

    print('edituser')
    output = {'response': False}
    con = connectdb()

    if con == False:
        output['message'] = 'No se puede conectar a la BD'
        return jsonify(output), 401

    cur = con.cursor()
    inputIn = request.get_json(silent=True)

    print('Se valida JSON de entrada')
    if inputIn is not None:
        print('Hay un JSON de entrada')

        # id usuario
        id = getInput(validateJson(inputIn, 'id'))
        if id == False:
            output['id'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

        # nombres
        nombres = getInput(validateJson(inputIn, 'nombres'))
        if nombres == False:
            output['nombres'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

        # apellidos
        apellidos = getInput(validateJson(inputIn, 'apellidos'))
        if apellidos == False:
            output['fechaestudios'] = 'No se proporciono el campo o esta vacio'
            return jsonify(output), 400

        # Email
        email= validateJson(inputIn, 'email')
        if email == False:
            output['email'] = 'No se proporciono el array o esta vacio'
            return jsonify(output), 400

        # Tipo
        tipo = validateJson(inputIn, 'tipo')
        if tipo == False:
            output['tipo'] = 'No se proporciono el array o esta vacio'
            return jsonify(output), 400

        # Telefono
        telefono = validateJson(inputIn, 'telefono')
        if telefono == False:
            output['telefono'] = 'No se proporciono el array o esta vacio'
            return jsonify(output), 400

        # Descripcion
        descripcion = validateJson(inputIn, 'descripcion')
        if descripcion == False:
            output['descripcion'] = 'No se proporciono el array o esta vacio'
            return jsonify(output), 400

    else:
        print('No se proporciono JSON')
        output['body'] = 'No se proporciono body'
        return jsonify(output), 400

    try:

        query = f"select * from usuario where id = {id}"
        print(query)
        cur.execute(query)
        usuario = cur.fetchone()
        print(usuario)

        if usuario is None:
            print('El id de usuario no existe en la base de datos')
            con.commit()
            cur.close()
            con.close()
            output['message'] = 'El id de usuario no existe en la base de datos'
            return jsonify(output), 202

        else:

            try:

                print('Se hace update a la tabla usuario')
                query = f"update usuario set nombres = '{nombres}', apellidos = '{apellidos}', email = '{email}', " \
                        f"tipo = '{tipo}', telefono = '{telefono}', descripcion = '{descripcion}' where " \
                        f"id = {id}"
                print(query)
                cur.execute(query)

            except Exception as e:
                print(e)
                print('Ocurrio un error al realizar el update del usuario')
                output['message'] = 'Ocurrio un error al realizar el update del usuario'
                return jsonify(output), 500

    except Exception as e:
        print(e)
        print('Ocurrio un error al validar el id del usuario')
        output['message'] = 'Ocurrio un error al validar el id del usuario'
        return jsonify(output), 500

    output['message'] = 'Se actualizaron correctamente los datos del usuario'
    output['response'] = True
    con.commit()
    cur.close()
    con.close()
    print('Ejecucion correcta')
    return jsonify(output), 200


'#----------------------------------------------------Borrar usuario logicamente-------------------------------------'


@app.route("/login/deluser/<id>", methods=['GET'])
@token_user
@cross_origin(supports_credentials=True)
def deluser(id):

    print('deluser')
    output = {'response': False}
    con = connectdb()
    cur = con.cursor()

    try:
        print('Se hace select a la tabla estudios para validar  el id de usuario')
        query = f"select * from usuario where id = {id}"
        print(query)
        cur.execute(query)
        usuario = cur.fetchone()
        print(usuario)

        if usuario is None:
            print('El id de usuario no existe en la base de datos')
            con.commit()
            cur.close()
            con.close()
            output['message'] = 'El id de usuario no existe en la base de datos'
            return jsonify(output), 202

        else:

            try:

                fecha_hoy = datetime.datetime.today().strftime('%Y-%m-%d %H:%M')
                print('Se hace update a la tabla usuario')
                query = f"update usuario set eliminado = true, fecha_eliminacion= '{fecha_hoy}' where id = {id}"
                print(query)
                cur.execute(query)

            except Exception as e:
                print(e)
                print('Ocurrio un error  al eliminar el usuario')
                output['message'] = 'Ocurrio un error  al eliminar el usuario'
                return jsonify(output), 500

    except Exception as e:
        print(e)
        print('Error al borrar el usuario  ')
        output['message'] = 'Error al borrar el usuario'
        return jsonify(output), 500

    output['message'] = 'Se elimino correctamente el usuario'
    output['response'] = True
    con.commit()
    cur.close()
    con.close()
    print('Ejecucion correcta')
    return jsonify(output), 200


'#----------------------------------------Obtener todos los usuarios eliminados------------------------------------'


@app.route("/login/getusersdel", methods=['GET'])
@token_user
@cross_origin(supports_credentials=True)
def getusersdel():

    print('getusersdel')
    output = {'response': False}
    usuariosarray = []

    con = connectdb()
    if con == False:
        output['message'] = 'No se puede conectar a la BD'
        return jsonify(output), 401

    cur = con.cursor()

    try:

        print('Se realiza consulta a la base para buscar los usuarios creados')
        query = f"select * from usuario where eliminado = true order by fecha_eliminacion DESC"
        print(query)
        cur.execute(query)
        usuarios = cur.fetchall()
        print(usuarios)

        if usuarios is None or usuarios == []:
            print('No se encontraron usuarios')

        else:
            print('Se encontraron los usuarios eliminados iterar en ellos')
            j = 0
            for i in usuarios:
                j = j+1
                print('Usuario eliminado #', str(j) + ':', i)
                id = i[0]
                nombres = i[1]
                apellidos = i[2]
                email = i[3]
                tipo = i[5]
                telefono = i[6]
                descripcion = i[7]
                fechacreacion = i[9].strftime('%Y-%m-%d %H:%M')
                fechaeliminacion = i[10].strftime('%Y-%m-%d %H:%M')

                iObj = {

                    'id': id,
                    'nombres': nombres,
                    'apellidos': apellidos,
                    'email': email,
                    'tipo': tipo,
                    'telefono': telefono,
                    'descripcion': descripcion,
                    'fechacreacion': fechacreacion,
                    'fechaeliminacion': fechaeliminacion,

                }
                usuariosarray.append(iObj)
            else:
                print('Se obtuvieron los usuarios eliminados')

        output['Usuarios'] = usuariosarray

    except Exception as e:
        print(e)
        print('Ocurrio un error al obtener los usuarios eliminados')
        output['message'] = 'Ocurrio un error al obtener los usuarios eliminados '
        return jsonify(output), 500

    output['message'] = 'Se obtuvieron correctamente los usuarios eliminados '
    output['response'] = True
    con.commit()
    cur.close()
    con.close()
    print('Ejecucion correcta')
    return jsonify(output), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4000, debug=True)