import psycopg2
import psycopg2.extras


class DBManager:
    def __init__(self):
        # CONFIGURACIÓN: Revisa que Mi_Base_Local esté exactamente así en pgAdmin
        self.params = {
            "host": "127.0.0.1",
            "database": "postgres",
            "user": "postgres",
            "password": "080810",  # <--- CAMBIA ESTO POR: 080810
            "port": "5432"
        }

    def ejecutar(self, query, params=None, fetch=False):
        conexion = None
        try:
            # Intentamos conectar con un tiempo de espera corto
            conexion = psycopg2.connect(**self.params, connect_timeout=3)
            cursor = conexion.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor)

            # Forzamos UTF8
            cursor.execute("SET client_encoding TO 'UTF8';")

            cursor.execute(query, params)

            resultado = None
            if fetch:
                resultado = cursor.fetchall()
            else:
                conexion.commit()
                resultado = True

            cursor.close()
            return resultado

        except Exception as e:
            # --- EL FILTRO DE EMERGENCIA PARA HUGO ---
            # Si el error trae tildes raras, esto las borra y deja solo el texto limpio
            try:
                # Convertimos el error a texto ignorando caracteres extraños
                error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
            except:
                error_msg = "Error de conexion (Revisa nombre de DB o Clave)"

            print(f"\n--- MENSAJE FINAL (SIN TILDES) ---")
            print(f"Detalle: {error_msg}")
            print(f"----------------------------------\n")
            return None

        finally:
            if conexion:
                conexion.close()
