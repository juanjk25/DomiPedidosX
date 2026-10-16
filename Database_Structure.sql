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
CREATE TABLE Empleados(
    id_empleado SERIAL PRIMARY KEY,
    cedula_empleado VARCHAR(20) UNIQUE NOT NULL,
    nombre_empleado VARCHAR(50) NOT NULL,
    apellido_empleado VARCHAR(50) NOT NULL,
    
    fecha_nacimiento DATE NOT NULL,

    cargo VARCHAR(30) NOT NULL,
    CHECK(cargo IN ('Cajero','Aseador','Cocinero')),
    salario NUMERIC(12,2)
    NOT NULL CHECK(salario>0),

    fecha_contrato DATE DEFAULT CURRENT_DATE,

    telefono_empleado VARCHAR(15),
    correo_empleado VARCHAR(100) UNIQUE,

    id_sede INT NOT NULL,

    FOREIGN KEY(id_sede)
    REFERENCES Sedes(id_sede),

    CHECK(
        fecha_nacimiento <=
        CURRENT_DATE - INTERVAL '18 years'
    )
);
CREATE TABLE Administrador(
    id_administrador SERIAL PRIMARY KEY,
    cedula_administrador VARCHAR(20) UNIQUE NOT NULL,
    nombre_administrador VARCHAR(50) NOT NULL,
    apellido_administrador VARCHAR(50) NOT NULL,

    fecha_nacimiento DATE NOT NULL,

    cargo VARCHAR(30) NOT NULL,
    CHECK(cargo IN ('Administrativo','Operador Local','Contador')),
    salario NUMERIC(12,2)
    NOT NULL CHECK(salario>0),

    fecha_contrato DATE DEFAULT CURRENT_DATE,

    telefono_administrador VARCHAR(15),
    correo_administrador VARCHAR(100) UNIQUE,

    id_sede INT NOT NULL,

    FOREIGN KEY(id_sede)
    REFERENCES Sedes(id_sede),

    CHECK(
        fecha_nacimiento <=
        CURRENT_DATE - INTERVAL '18 years'
    )
);

CREATE TABLE Inventario(
    id_inventario SERIAL PRIMARY KEY,

    id_producto INT NOT NULL,
    id_sede INT NOT NULL,

    cantidad_disponible INT
    DEFAULT 0 CHECK(cantidad_disponible>=0),

    stock_minimo INT
    DEFAULT 10 CHECK(stock_minimo>=0),

    stock_maximo INT DEFAULT 1000,

    FOREIGN KEY(id_producto)
    REFERENCES Productos(id_producto),

    FOREIGN KEY(id_sede)
    REFERENCES Sedes(id_sede),

    UNIQUE(id_producto,id_sede),

    CHECK(stock_maximo>=stock_minimo)
);
CREATE TABLE Repartidor(
    id_repartidor SERIAL PRIMARY KEY,
    cedula_repartidor VARCHAR(20) UNIQUE NOT NULL,
    nombre_repartidor VARCHAR(50) NOT NULL,
    apellido_repartidor VARCHAR(50) NOT NULL,
    telefono_repartidor VARCHAR(20) UNIQUE NOT NULL,
    tipo_vehiculo VARCHAR(30) NOT NULL CHECK (tipo_vehiculo IN ('Moto', 'Bicicleta', 'Carro')),
    placa_vehiculo VARCHAR(15) NOT NULL, 
    estado_operativo VARCHAR(20) DEFAULT 'Inactivo' CHECK (estado_operativo IN ('Disponible', 'Ocupado', 'Inactivo')),
    ultima_actualizacion_gps TIMESTAMP,
);
CREATE TABLE Pedido(
    id_pedido SERIAL PRIMARY KEY,
    
    id_cliente INT NOT NULL,
    id_sede INT NOT NULL,
    id_repartidor INT, -- NULL al inicio, se actualiza cuando un motorizado acepta el viaje
    
    estado_pedido VARCHAR(30) NOT NULL DEFAULT 'Pendiente'
    CHECK(estado_pedido IN ('Pendiente', 'Preparando', 'En Camino', 'Entregado', 'Cancelado')),
    
    -- La dirección de entrega puede ser distinta a la de residencia del cliente
    direccion_entrega VARCHAR(150) NOT NULL,
    notas_cliente TEXT,
    
    fecha_hora_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tiempo_estimado_entrega TIMESTAMP, 

    FOREIGN KEY(id_cliente) REFERENCES Cliente(id_cliente),
    FOREIGN KEY(id_sede) REFERENCES Sedes(id_sede),
    FOREIGN KEY(id_repartidor) REFERENCES Repartidor(id_repartidor)
);
CREATE TABLE Factura(
    id_factura SERIAL PRIMARY KEY,
    numero_factura_oficial VARCHAR(50) UNIQUE NOT NULL,
    
    -- Se vincula directamente al pedido (Relación 1 a 1)
    id_pedido INT UNIQUE NOT NULL,
    
    -- El empleado que cobra (el cajero), no el que reparte
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
    FOREIGN KEY(id_empleado) REFERENCES Empleados(id_empleado),
    
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
