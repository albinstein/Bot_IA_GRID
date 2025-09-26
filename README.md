# Bot IA GRID

## Descripción general
Bot IA GRID es un bot de trading de rejilla (grid) para mercados **spot** que genera y gestiona órdenes utilizando una progresión geométrica de precios. El objetivo es capturar la volatilidad lateral del mercado configurando un conjunto de niveles de compra y venta equidistantes en términos relativos. El bot puede operar tanto en modo en vivo como sobre datos históricos para backtesting.

## Supuestos de operación
- El bot opera únicamente en mercados spot y **no utiliza margen ni apalancamiento**.
- Todas las operaciones se realizan contra un único par de activos base/contrapartida configurado por el usuario.
- Se asume que la cuenta de intercambio dispone de saldo suficiente para cubrir todas las órdenes simultáneas calculadas por la rejilla.
- Las comisiones y deslizamientos son parámetros configurables que deben ser aportados por el usuario en función del intercambio utilizado.

## Dependencias y requisitos del entorno
- Python **3.10 o superior**.
- [pandas](https://pandas.pydata.org/) para la manipulación de datos de mercado.
- (Opcional) `python-dotenv` para gestionar credenciales a través de archivos `.env`.
- Se recomienda crear un entorno virtual con `venv` o `conda` para aislar las dependencias del sistema.

Instalación recomendada en un entorno virtual `venv`:

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt  # si está disponible
```

Si no existe un archivo `requirements.txt`, instale manualmente las dependencias mínimas:

```bash
pip install pandas python-dotenv
```

## Limitaciones conocidas
- El bot no ejecuta estrategias de cobertura ni protección de pérdidas.
- No se implementa gestión avanzada de riesgo más allá del dimensionamiento fijo de la rejilla.
- Los resultados del backtesting dependen completamente de la calidad de los datos históricos proporcionados.
- No incorpora manejo de posiciones cortas ni derivados.

## Ejemplos de uso

### Uso como paquete de Python
El siguiente ejemplo mínimo muestra cómo inicializar el bot y generar órdenes basadas en una configuración simple:

```python
from bot_ia_grid.bot import GeometricGridBot
from bot_ia_grid.config import GridConfig

config = GridConfig(
    symbol="BTCUSDT",
    levels=10,
    lower_price=25000,
    upper_price=35000,
    quote_balance=1000.0,
)

bot = GeometricGridBot(config)
bot.initialize_grid()
orders = bot.generate_orders()
for order in orders:
    print(order)
```

### Script `examples/demo_grid_bot.py`
El repositorio incluye un script de ejemplo que ejecuta la estrategia con parámetros predefinidos. Para utilizarlo:

```bash
python examples/demo_grid_bot.py \
    --symbol BTCUSDT \
    --levels 10 \
    --lower-price 25000 \
    --upper-price 35000 \
    --quote-balance 1000
```

El script imprime por consola la rejilla generada y, si se proporcionan credenciales de intercambio mediante variables de entorno, puede enviar las órdenes correspondientes. Consulte los comentarios del script para conocer todas las opciones disponibles.

## Ejecución de pruebas automatizadas
La suite de pruebas utiliza [pytest](https://docs.pytest.org/). Tras instalar las dependencias y activar el entorno virtual, ejecute:

```bash
pytest
```

Puede agregar la opción `-m` o `-k` para filtrar pruebas específicas.

Si es la primera vez que clona el proyecto, asegúrese de instalar las dependencias antes de lanzar las pruebas:

```bash
pip install pytest pandas
```

---
> ⚠️ **Aviso**: El trading conlleva riesgos significativos. Utilice el bot bajo su propia responsabilidad y verifique siempre los parámetros antes de operar en producción.
