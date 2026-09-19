import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from database import GestorBaseDatos

TEMA_OSCURO = "darkly"
TEMA_CLARO = "litera"

ORDEN_DISPLAY_A_CLAVE = {
    "ID": ("id", "ASC"),
    "Nombre (Z-A)": ("nombre", "DESC"),
    "Precio": ("precio", "ASC"),
    "Stock": ("cantidad", "ASC"),
}


class GuardianInventarioApp:

    def __init__(self, root):
        self.db = GestorBaseDatos()
        self.root = root
        self.style = ttk.Style()
        self.root.title("El Guardián del Inventario")
        self.root.geometry("1150x780")

        self.nombre_var = tk.StringVar()
        self.precio_var = tk.StringVar()
        self.cantidad_var = tk.StringVar()
        self.minimo_var = tk.StringVar()
        self.total_productos_var = tk.StringVar(value="0 Units")
        self.valor_inventario_var = tk.StringVar(value="$ 0")
        self.total_registrados_var = tk.StringVar(value="0")
        self.alertas_var = tk.StringVar(value="0")
        self.top_valor_var = tk.StringVar(value="—")
        self.busqueda_var = tk.StringVar()
        self.orden_var = tk.StringVar(value="ID")
        self.producto_seleccionado_id = None
        self.vista_actual = "todos"
        self.modo_oscuro = True

        self._construir_layout()
        self._actualizar_texto_tema()
        self.actualizar_vistas()

        self.busqueda_var.trace_add("write", lambda *args: self._refrescar_vista_actual())

    def _construir_layout(self):
        header = ttk.Frame(self.root, bootstyle="primary", padding=15)
        header.pack(fill="x")
        ttk.Label(header, text="EL GUARDIÁN DEL INVENTARIO", bootstyle="inverse-primary", font=("Segoe UI", 16, "bold")).pack(side="left")
        self.btn_tema = ttk.Button(header, command=self.cambiar_tema, bootstyle="secondary-outline", padding=(8, 2))
        self.btn_tema.pack(side="right", padx=10)
        self.style.configure(self.btn_tema.cget("style"), font=("Segoe UI", 9))

        main_container = ttk.Frame(self.root, padding=(40, 20))
        main_container.pack(fill="both", expand=True)

        stats_frame = ttk.Frame(main_container)
        stats_frame.pack(fill="x", pady=(0, 20))

        self._crear_tarjeta(stats_frame, "TOTAL PRODUCTOS EN STOCK", self.total_productos_var, "info")
        self._crear_tarjeta(stats_frame, "VALOR TOTAL DEL INVENTARIO", self.valor_inventario_var, "warning")
        self._crear_tarjeta(stats_frame, "PRODUCTOS REGISTRADOS", self.total_registrados_var, "secondary")
        self.card_alertas, self.titulo_alertas, self.label_alertas = self._crear_tarjeta(stats_frame, "ALERTAS DE STOCK BAJO", self.alertas_var, "secondary")
        self._crear_tarjeta(stats_frame, "PRODUCTO DE MAYOR VALOR", self.top_valor_var, "secondary")

        control_frame = ttk.Labelframe(main_container, text=" Registro y Edición ", bootstyle="info", padding=15)
        control_frame.pack(fill="x", pady=(0, 20))

        ttk.Label(control_frame, text="Nombre del Producto", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=10, pady=(0, 5), sticky="w")
        ttk.Entry(control_frame, textvariable=self.nombre_var).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew", columnspan=3)

        ttk.Label(control_frame, text="Precio Venta (COP)", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, padx=10, pady=(0, 5), sticky="w")
        ttk.Label(control_frame, text="Cantidad actual", font=("Segoe UI", 9, "bold")).grid(row=2, column=1, padx=10, pady=(0, 5), sticky="w")
        ttk.Label(control_frame, text="Mínimo Seguridad", font=("Segoe UI", 9, "bold")).grid(row=2, column=2, padx=10, pady=(0, 5), sticky="w")

        ttk.Entry(control_frame, textvariable=self.precio_var, justify="center").grid(row=3, column=0, padx=10, sticky="ew")
        ttk.Entry(control_frame, textvariable=self.cantidad_var, justify="center").grid(row=3, column=1, padx=10, sticky="ew")
        ttk.Entry(control_frame, textvariable=self.minimo_var, justify="center").grid(row=3, column=2, padx=10, sticky="ew")

        control_frame.columnconfigure(0, weight=2)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)

        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(action_frame, text="GUARDAR", command=self.agregar, bootstyle="success").pack(side="left", padx=(0, 5))
        ttk.Button(action_frame, text="ACTUALIZAR", command=self.actualizar, bootstyle="info").pack(side="left", padx=5)
        ttk.Button(action_frame, text="ELIMINAR", command=self.eliminar, bootstyle="danger").pack(side="left", padx=5)
        ttk.Button(action_frame, text="LIMPIAR", command=self.limpiar_campos, bootstyle="secondary").pack(side="left", padx=5)

        ttk.Button(action_frame, text="TODOS", command=self.listar_productos, bootstyle="dark").pack(side="right", padx=(5, 0))
        ttk.Button(action_frame, text="URGENCIAS ⚠", command=self.listar_urgentes, bootstyle="warning").pack(side="right", padx=5)

        filtro_frame = ttk.Frame(main_container)
        filtro_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(filtro_frame, text="Buscar:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
        ttk.Entry(filtro_frame, textvariable=self.busqueda_var, width=30).pack(side="left", padx=(0, 20))

        ttk.Label(filtro_frame, text="Ordenar por:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
        combo_orden = ttk.Combobox(filtro_frame, textvariable=self.orden_var, values=list(ORDEN_DISPLAY_A_CLAVE.keys()), state="readonly", width=10)
        combo_orden.pack(side="left")
        combo_orden.bind("<<ComboboxSelected>>", lambda e: self._refrescar_vista_actual())

        tree_frame = ttk.Frame(main_container)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Nombre", "Precio", "Cantidad", "Min"), show="headings", bootstyle="info")
        self.tree.heading("ID", text="ID"); self.tree.column("ID", width=40, anchor="center")
        self.tree.heading("Nombre", text="Producto"); self.tree.column("Nombre", width=350)
        self.tree.heading("Precio", text="Precio Unitario"); self.tree.column("Precio", width=120, anchor="e")
        self.tree.heading("Cantidad", text="Stock"); self.tree.column("Cantidad", width=80, anchor="center")
        self.tree.heading("Min", text="Mínimo"); self.tree.column("Min", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview, bootstyle="round")
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_item)

    def _crear_tarjeta(self, parent, titulo, variable, estilo="secondary", tamano=15):
        card = ttk.Frame(parent, bootstyle=estilo, padding=12)
        card.pack(side="left", expand=True, fill="x", padx=4)
        inverso = f"inverse-{estilo}"
        label_titulo = ttk.Label(card, text=titulo, bootstyle=inverso, font=("Segoe UI", 8, "bold"))
        label_titulo.pack()
        label_valor = ttk.Label(card, textvariable=variable, bootstyle=inverso, font=("Segoe UI", tamano, "bold"))
        label_valor.pack()
        return card, label_titulo, label_valor

    def _actualizar_texto_tema(self):
        self.btn_tema.configure(text="☀️ Modo claro" if self.modo_oscuro else "🌙 Modo oscuro")

    def cambiar_tema(self):
        self.modo_oscuro = not self.modo_oscuro
        self.style.theme_use(TEMA_OSCURO if self.modo_oscuro else TEMA_CLARO)
        self._actualizar_texto_tema()
        self._refrescar_vista_actual()

    def _actualizar_color_alertas(self):
        urgentes = self.db.contar_urgentes()
        estilo = "warning" if urgentes > 0 else "secondary"
        self.card_alertas.configure(bootstyle=estilo)
        self.titulo_alertas.configure(bootstyle=f"inverse-{estilo}")
        self.label_alertas.configure(bootstyle=f"inverse-{estilo}")

    def _color_urgente(self):
        return "#3a2a12" if self.modo_oscuro else "#FDEBD0"

    def _formatear_cop(self, valor):
        return "$ {:,.0f}".format(float(valor or 0))

    def actualizar_vistas(self):
        self._refrescar_vista_actual()
        cant_total, valor_total = self.db.obtener_resumen_financiero()
        self.total_productos_var.set(f"{int(cant_total)} Units")
        self.valor_inventario_var.set(self._formatear_cop(valor_total))

        self.total_registrados_var.set(str(self.db.contar_productos()))

        urgentes = self.db.contar_urgentes()
        self.alertas_var.set(str(urgentes))
        self._actualizar_color_alertas()

        nombre_top, precio_top = self.db.obtener_producto_mas_valioso()
        self.top_valor_var.set(f"{nombre_top} ({self._formatear_cop(precio_top)})" if nombre_top else "—")

    def validar_entradas(self):
        try:
            if not self.nombre_var.get(): raise ValueError
            float(self.precio_var.get()); int(self.cantidad_var.get()); int(self.minimo_var.get())
            return True
        except (ValueError, TypeError):
            messagebox.showwarning("Error", "Datos inválidos. Verifique los campos numéricos.")
            return False

    def _orden_actual(self):
        return ORDEN_DISPLAY_A_CLAVE.get(self.orden_var.get(), ("id", "ASC"))

    def _refrescar_vista_actual(self):
        columna, direccion = self._orden_actual()
        texto = self.busqueda_var.get().strip()
        if texto:
            registros = self.db.buscar_por_nombre(texto, columna, direccion)
        elif self.vista_actual == "urgentes":
            registros = self.db.obtener_urgentes(columna, direccion)
        else:
            registros = self.db.obtener_todos(columna, direccion)
        self._llenar_tabla(registros)

    def listar_productos(self):
        self.vista_actual = "todos"
        self.busqueda_var.set("")
        self._refrescar_vista_actual()

    def listar_urgentes(self):
        self.vista_actual = "urgentes"
        self.busqueda_var.set("")
        self._refrescar_vista_actual()

    def _llenar_tabla(self, registros):
        for row in self.tree.get_children(): self.tree.delete(row)
        self.tree.tag_configure('urgente', background=self._color_urgente())
        for row in registros:
            item_id = self.tree.insert("", tk.END, values=(row[0], row[1], self._formatear_cop(row[2]), row[3], row[4]))
            if row[3] <= row[4]: self.tree.item(item_id, tags=('urgente',))

    def agregar(self):
        if self.validar_entradas():
            self.db.agregar_producto(self.nombre_var.get(), float(self.precio_var.get()), int(self.cantidad_var.get()), int(self.minimo_var.get()))
            self.limpiar_campos()
            self.actualizar_vistas()

    def actualizar(self):
        if self.producto_seleccionado_id and self.validar_entradas():
            self.db.actualizar_producto(self.producto_seleccionado_id, self.nombre_var.get(), float(self.precio_var.get()), int(self.cantidad_var.get()), int(self.minimo_var.get()))
            self.limpiar_campos()
            self.actualizar_vistas()

    def eliminar(self):
        if self.producto_seleccionado_id and messagebox.askyesno("Confirmar", "¿Eliminar producto?"):
            self.db.eliminar_producto(self.producto_seleccionado_id)
            self.limpiar_campos()
            self.actualizar_vistas()

    def seleccionar_item(self, event):
        seleccion = self.tree.selection()
        if seleccion:
            datos = self.tree.item(seleccion)['values']
            self.producto_seleccionado_id = datos[0]
            self.nombre_var.set(datos[1])
            self.precio_var.set(str(datos[2]).replace("$", "").replace(",", "").strip())
            self.cantidad_var.set(datos[3])
            self.minimo_var.set(datos[4])

    def limpiar_campos(self):
        self.nombre_var.set(""); self.precio_var.set(""); self.cantidad_var.set(""); self.minimo_var.set("")
        self.producto_seleccionado_id = None