# Optimización-de-Ventas-y-Analisis-de-Datos---La-Reyna-POS
Sistema de Gestión Transaccional y Business Intelligence
# Informe Técnico: Optimización de Ventas y Análisis de Datos - La Reyna POS
**Desarrollador:** Hugo González González  
**Proyecto:** Sistema de Gestión Transaccional y Business Intelligence

## 1. Resumen Ejecutivo
Este proyecto surge de la necesidad de digitalizar las operaciones de venta de productos deportivos (como la **Camiseta Deportiva LDA**) y automatizar el control de inventarios. El sistema no solo procesa pagos, sino que estructura la información para un análisis posterior de comportamiento de compra.

## 2. Arquitectura de Visualización de Datos
Como se observa en la interfaz de métricas, el sistema desglosa los ingresos para permitir un control financiero estricto.

### 2.1 Análisis de Flujo de Ingresos
El sistema rastrea las ventas en tiempo real, permitiendo identificar picos de actividad según la hora y el día.

![Gráfico de Flujo de Ingresos](./Captura%20de%20pantalla%202026-03-25%20194358.png)
*Figura 1: Visualización del acumulado de ventas (₡200,000) y unidades vendidas.*

### 2.2 Segmentación por Métodos de Pago
Dada la relevancia de los pagos digitales en Costa Rica, la aplicación separa automáticamente las transacciones en **Efectivo, SINPE Móvil y Tarjeta**.
