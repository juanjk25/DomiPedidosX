CREATE TABLE Departamentos(
    id_departamento SERIAL PRIMARY KEY,
    nombre_departamento VARCHAR(50) UNIQUE NOT NULL
);
CREATE TABLE Ciudad(
    id_ciudad BIGSERIAL PRIMARY KEY,
    nombre_ciudad VARCHAR(50) UNIQUE NOT NULL,
    id_departamento INT NOT NULL,

    FOREIGN KEY(id_departamento)
    REFERENCES Departamentos(id_departamento)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,


);
CREATE TABLE Cliente(
    id_cliente BIGSERIAL PRIMARY KEY,
    tipo_documento VARCHAR(5) NOT NULL
    CHECK(tipo_documento IN ('CC','CE','NIT','TI')),

    numero_documento VARCHAR(20) NOT NULL,
    nombres VARCHAR(50) NOT NULL,
    apellidos VARCHAR(50) NOT NULL,
    telefono_cliente VARCHAR(15),
    correo_cliente VARCHAR(100) UNIQUE,
    direccion_residencia VARCHAR(150),
    fecha_nacimiento DATE NOT NULL,

    CONSTRAINT uq_documento_cliente
    UNIQUE(tipo_documento,numero_documento)
);
CREATE TABLE Productos(
    id_producto SERIAL PRIMARY KEY,
    codigo_de_barras VARCHAR(30) UNIQUE NOT NULL,
    nombre_producto VARCHAR(80) NOT NULL,
    tipo_de_producto VARCHAR(50) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    precio_compra NUMERIC(12,2)
    NOT NULL CHECK(precio_compra>0),

    precio_venta NUMERIC(12,2)
    NOT NULL CHECK(precio_venta>0),

    CONSTRAINT chk_margen_operativo
    CHECK(precio_venta>=precio_compra)
    );
CREATE TABLE Sedes(
    id_sede SERIAL PRIMARY KEY,
    nombre_sede VARCHAR(50) NOT NULL,
    barrio_sede VARCHAR(50) NOT NULL,
    id_ciudad INT NOT NULL,
    direccion VARCHAR (100) UNIQUE NOT NULL,

    horario_atencion_apertura TIME NOT NULL,
    horario_atencion_cierre TIME NOT NULL,

    FOREIGN KEY(id_ciudad)
    REFERENCES Ciudad(id_ciudad)
);

CREATE TABLE Empleado(
    id_empleado SERIAL PRIMARY KEY,
    cedula_empleado VARCHAR(20) UNIQUE NOT NULL,
    nombre_empleado VARCHAR(50) NOT NULL,
    apellido_empleado VARCHAR(50) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    telefono_empleado VARCHAR(15),
    correo_empleado VARCHAR(100) UNIQUE,
    fecha_contrato DATE DEFAULT CURRENT_DATE,
    salario NUMERIC(12,2) NOT NULL CHECK(salario>0),
    tipo_empleado VARCHAR(20) NOT NULL CHECK(tipo_empleado IN ('Cajero', 'Repartidor', 'Operador_Sede')),

    CHECK(
        fecha_nacimiento <=
        CURRENT_DATE - INTERVAL '18 years'
    )
);

CREATE TABLE Cajero(
    id_empleado INT PRIMARY KEY,
    id_sede INT NOT NULL,

    FOREIGN KEY(id_empleado) REFERENCES Empleado(id_empleado) ON DELETE CASCADE,
    FOREIGN KEY(id_sede) REFERENCES Sedes(id_sede)
);

CREATE TABLE Repartidor(
    id_empleado INT PRIMARY KEY,
    tipo_vehiculo VARCHAR(30) NOT NULL CHECK (tipo_vehiculo IN ('Moto', 'Bicicleta', 'Carro')),
    placa_vehiculo VARCHAR(15) NOT NULL, 
    estado_operativo VARCHAR(20) DEFAULT 'Inactivo' CHECK (estado_operativo IN ('Disponible', 'Ocupado', 'Inactivo')),
    ultima_actualizacion_gps TIMESTAMP,

    FOREIGN KEY(id_empleado) REFERENCES Empleado(id_empleado) ON DELETE CASCADE
);

CREATE TABLE Operador_Sede(
    id_empleado INT PRIMARY KEY,
    id_sede INT NOT NULL,
    cargo_operativo VARCHAR(30) NOT NULL CHECK(cargo_operativo IN ('Administrativo','Operador Local','Contador')),

    FOREIGN KEY(id_empleado) REFERENCES Empleado(id_empleado) ON DELETE CASCADE,
    FOREIGN KEY(id_sede) REFERENCES Sedes(id_sede)
);

CREATE TABLE Ingredientes(
    id_ingrediente SERIAL PRIMARY KEY,
    nombre_ingrediente VARCHAR(100) NOT NULL,
    descripcion_ingrediente TEXT,
    unidad_medida VARCHAR(20) NOT NULL CHECK(unidad_medida IN ('kg', 'g', 'L', 'ml', 'unidad', 'paquete')),
    estado_disponibilidad BOOLEAN DEFAULT TRUE
);

CREATE TABLE Sede_Ingrediente(
    id_sede INT NOT NULL,
    id_ingrediente INT NOT NULL,
    cantidad_disponible NUMERIC(10,2) DEFAULT 0 CHECK(cantidad_disponible>=0),
    stock_minimo NUMERIC(10,2) DEFAULT 10 CHECK(stock_minimo>=0),
    stock_maximo NUMERIC(10,2) DEFAULT 1000,

    PRIMARY KEY(id_sede, id_ingrediente),
    FOREIGN KEY(id_sede) REFERENCES Sedes(id_sede) ON DELETE CASCADE,
    FOREIGN KEY(id_ingrediente) REFERENCES Ingredientes(id_ingrediente) ON DELETE CASCADE,
    CHECK(stock_maximo>=stock_minimo)
);

CREATE TABLE Producto_Ingrediente(
    id_producto INT NOT NULL,
    id_ingrediente INT NOT NULL,
    cantidad_requerida NUMERIC(10,2) NOT NULL CHECK(cantidad_requerida>0),

    PRIMARY KEY(id_producto, id_ingrediente),
    FOREIGN KEY(id_producto) REFERENCES Productos(id_producto) ON DELETE CASCADE,
    FOREIGN KEY(id_ingrediente) REFERENCES Ingredientes(id_ingrediente) ON DELETE CASCADE
);

CREATE TABLE Pedido(
    id_pedido SERIAL PRIMARY KEY,
    
    id_cliente BIGINT NOT NULL,
    id_sede INT NOT NULL,
    id_repartidor INT, 
    
    estado_pedido VARCHAR(30) NOT NULL DEFAULT 'Pendiente'
    CHECK(estado_pedido IN ('Pendiente', 'Preparando', 'En Camino', 'Entregado', 'Cancelado')),
    
    direccion_entrega VARCHAR(150) NOT NULL,
    notas_cliente TEXT,
    
    fecha_hora_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tiempo_estimado_entrega TIMESTAMP, 

    FOREIGN KEY(id_cliente) REFERENCES Cliente(id_cliente),
    FOREIGN KEY(id_sede) REFERENCES Sedes(id_sede),
    FOREIGN KEY(id_repartidor) REFERENCES Repartidor(id_empleado)
);
CREATE TABLE Factura(
    id_factura SERIAL PRIMARY KEY,
    numero_factura_oficial VARCHAR(50) UNIQUE NOT NULL,
    
    id_pedido INT UNIQUE NOT NULL,
    id_empleado INT NOT NULL, 
    
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    forma_pago VARCHAR(20) NOT NULL CHECK(forma_pago IN ('EFECTIVO','DEBITO','CREDITO','BONO')),

    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK(subtotal>=0),
    total_iva NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK(total_iva>=0),
    total_descuento NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK(total_descuento>=0),
    valor_pagado NUMERIC(12,2) NOT NULL CHECK(valor_pagado>=0),
    total_factura NUMERIC(12,2),
    cambio_devuelto NUMERIC(12,2),

    FOREIGN KEY(id_pedido) REFERENCES Pedido(id_pedido),
    FOREIGN KEY(id_empleado) REFERENCES Cajero(id_empleado),
    
    CHECK(valor_pagado>=total_factura)
);
CREATE TABLE Detalle_Pedido(
    id_linea SERIAL PRIMARY KEY,
    
    id_pedido INT NOT NULL, -- Se vincula a la tabla Pedido
    id_producto INT NOT NULL,
    
    -- Campos base que ingresa el backend (La comanda)
    cantidad INT NOT NULL CHECK(cantidad>0),
    precio_unitario_aplicado NUMERIC(12,2) NOT NULL CHECK(precio_unitario_aplicado>=0),

    -- Campos calculados por el Trigger 
    subtotal_linea NUMERIC(12,2),
    iva_aplicado NUMERIC(12,2),

    -- Las llaves foráneas apuntan a Pedido en lugar de Factura
    FOREIGN KEY(id_pedido) REFERENCES Pedido(id_pedido) ON DELETE CASCADE,
    FOREIGN KEY(id_producto) REFERENCES Productos(id_producto),
    
    -- Un mismo producto no debería estar en dos líneas separadas en el mismo pedido
    UNIQUE(id_pedido, id_producto)
);
-- Función
CREATE OR REPLACE FUNCTION funcion_calcular_detalle_pedido()
RETURNS TRIGGER AS $$
DECLARE
    tasa_iva NUMERIC := 0.19; -- 19% de IVA
BEGIN
    -- 1. Calcula el subtotal (Cantidad x Precio)
    NEW.subtotal_linea := NEW.cantidad * NEW.precio_unitario_aplicado;
    
    -- 2. Calcula el IVA de esa línea
    NEW.iva_aplicado := NEW.subtotal_linea * tasa_iva;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger
CREATE TRIGGER trigger_detalle_pedido
BEFORE INSERT OR UPDATE ON Detalle_Pedido
FOR EACH ROW
EXECUTE FUNCTION funcion_calcular_detalle_pedido();

-- Función
CREATE OR REPLACE FUNCTION funcion_calcular_totales_factura()
RETURNS TRIGGER AS $$
BEGIN
    -- 1. Calcula el Total de la Factura (Subtotal + IVA - Descuento)
    NEW.total_factura := NEW.subtotal + NEW.total_iva - NEW.total_descuento;
    
    -- 2. Calcula el Cambio Devuelto (Lo que pagó el cliente menos el total)
    NEW.cambio_devuelto := NEW.valor_pagado - NEW.total_factura;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger
CREATE TRIGGER trigger_totales_factura
BEFORE INSERT OR UPDATE ON Factura
FOR EACH ROW
EXECUTE FUNCTION funcion_calcular_totales_factura();
