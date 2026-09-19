import sqlite3

COLUMNAS_ORDEN = {
    "id": "id",
    "nombre": "nombre COLLATE NOCASE",
    "precio": "precio",
    "cantidad": "cantidad",
}


class GestorBaseDatos:
    def __init__(self, db_name="inventory.db"):
        self.db_name = db_name
        self.conexion_inicial()

    def _ejecutar(self, query, parametros=()):
        """Consulta de escritura (insert/update/delete)."""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute(query, parametros)

    def _consultar(self, query, parametros=()):
        """Consulta de lectura, devuelve todas las filas."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute(query, parametros)
            return cursor.fetchall()

    def conexion_inicial(self):
        # sin AUTOINCREMENT para permitir la re-indexación manual
        query = """
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                cantidad INTEGER NOT NULL,
                stock_minimo INTEGER NOT NULL
            )
        """
        self._ejecutar(query)

    def reindexar_alfabeticamente(self):
        """Reasigna los IDs de todos los productos según el orden alfabético."""
        query_obtener = "SELECT nombre, precio, cantidad, stock_minimo FROM productos ORDER BY nombre COLLATE NOCASE ASC"
        productos = self._consultar(query_obtener)

        self._ejecutar("DELETE FROM productos")

        for indice, (nom, pre, cant, st_min) in enumerate(productos, start=1):
            query_insertar = "INSERT INTO productos (id, nombre, precio, cantidad, stock_minimo) VALUES (?, ?, ?, ?, ?)"
            self._ejecutar(query_insertar, (indice, nom, pre, cant, st_min))

    def obtener_resumen_financiero(self):
        query = "SELECT SUM(cantidad), SUM(precio * cantidad) FROM productos"
        resumen = self._consultar(query)[0]
        return (resumen[0] or 0, resumen[1] or 0)

    def agregar_producto(self, nombre, precio, cantidad, stock_minimo):
        # reordenamos tras insertar para que el ID quede alfabético
        query = "INSERT INTO productos (nombre, precio, cantidad, stock_minimo) VALUES (?, ?, ?, ?)"
        self._ejecutar(query, (nombre, precio, cantidad, stock_minimo))
        self.reindexar_alfabeticamente()

    def eliminar_producto(self, id_producto):
        query = "DELETE FROM productos WHERE id = ?"
        self._ejecutar(query, (id_producto,))
        self.reindexar_alfabeticamente()

    def actualizar_producto(self, id_producto, nombre, precio, cantidad, stock_minimo):
        # el nombre puede cambiar, así que la posición alfabética también
        query = """
            UPDATE productos 
            SET nombre = ?, precio = ?, cantidad = ?, stock_minimo = ? 
            WHERE id = ?
        """
        self._ejecutar(query, (nombre, precio, cantidad, stock_minimo, id_producto))
        self.reindexar_alfabeticamente()

    def _direccion(self, direccion):
        return "DESC" if str(direccion).upper() == "DESC" else "ASC"

    def obtener_todos(self, orden="id", direccion="ASC"):
        columna = COLUMNAS_ORDEN.get(orden, "id")
        return self._consultar(f"SELECT * FROM productos ORDER BY {columna} {self._direccion(direccion)}")

    def obtener_urgentes(self, orden="nombre", direccion="ASC"):
        columna = COLUMNAS_ORDEN.get(orden, "nombre COLLATE NOCASE")
        return self._consultar(f"SELECT * FROM productos WHERE cantidad <= stock_minimo ORDER BY {columna} {self._direccion(direccion)}")

    def buscar_por_nombre(self, texto, orden="id", direccion="ASC"):
        columna = COLUMNAS_ORDEN.get(orden, "id")
        query = f"SELECT * FROM productos WHERE nombre LIKE ? COLLATE NOCASE ORDER BY {columna} {self._direccion(direccion)}"
        return self._consultar(query, (f"%{texto}%",))

    def contar_productos(self):
        return self._consultar("SELECT COUNT(*) FROM productos")[0][0]

    def contar_urgentes(self):
        return self._consultar("SELECT COUNT(*) FROM productos WHERE cantidad <= stock_minimo")[0][0]

    def obtener_producto_mas_valioso(self):
        resultado = self._consultar("SELECT nombre, precio FROM productos ORDER BY precio DESC LIMIT 1")
        return resultado[0] if resultado else (None, 0)