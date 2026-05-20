import pandas as pd
import csv
import io
import re

def normalize_csv(file_obj) -> tuple[pd.DataFrame, dict]:
    """
    Parser robusto para CSVs de índices satelitales.
    """
    # 1. Leer bytes y detectar encoding
    raw_data = file_obj.read()
    try:
        content = raw_data.decode('utf-8')
    except UnicodeDecodeError:
        content = raw_data.decode('latin-1')
    
    # 2. Detectar separador
    try:
        dialect = csv.Sniffer().sniff(content[:10000], delimiters=',;\t')
        sep = dialect.delimiter
    except:
        sep = ','
    
    # 3. Manejar decimales (si , es decimal, reemplazar por .)
    # Solo si el separador no es ,
    if sep != ',':
        # Intento detectar si hay comas que actúan como decimales
        # Si hay muchos patrones tipo digito,digito
        if len(re.findall(r'\d,\d', content)) > len(re.findall(r'\d\.\d', content)):
            content = content.replace(',', '.')
    
    # 4. Cargar DataFrame
    df = pd.read_csv(io.StringIO(content), sep=sep)
    
    # Limpiar espacios en blanco en los nombres de las columnas
    df.columns = [str(c).strip() for c in df.columns]
    
    # 5. Normalizar Nombres de Columnas
    metadata = {
        "n_fechas": 0,
        "indices_encontrados": [],
        "fecha_inicio": "",
        "fecha_fin": "",
        "warnings": []
    }
    
    col_map = {}
    # Expandir patrones de fecha para mayor compatibilidad
    date_patterns = [
        'fecha', 'date', 'time', 'timestamp', 'periodo', 'period', 'year', 'anio', 
        'dia', 'day', 'system:time_start', 'momento', 'tiempo'
    ]
    index_patterns = {
        'NDVI': ['ndvi', 'normalized_difference_vegetation_index'],
        'NDRE': ['ndre', 'normalized_difference_red_edge'],
        'EVI': ['evi', 'enhanced_vegetation_index'],
        'NDWI': ['ndwi', 'normalized_difference_water_index']
    }
    
    found_date_col = None
    for col in df.columns:
        col_lower = col.lower()
        
        # Detectar Fecha (prioridad absoluta)
        if any(p == col_lower or p in col_lower for p in date_patterns):
            if found_date_col is None: # Tomar la primera columna que parezca fecha
                found_date_col = col
                col_map[col] = 'fecha'
            continue
            
        # Detectar Índices
        for idx, patterns in index_patterns.items():
            if any(p in col_lower for p in patterns):
                if idx not in metadata["indices_encontrados"]:
                    col_map[col] = idx
                    metadata["indices_encontrados"].append(idx)
                elif any(s in col_lower for s in ['_mean', '_median', '_p50', 'average', 'promedio']):
                    # Priorizar versiones agregadas
                    prev_col = [k for k, v in col_map.items() if v == idx][0]
                    if prev_col in col_map: del col_map[prev_col]
                    col_map[col] = idx

    if not found_date_col:
        cols_found = ", ".join(df.columns[:5])
        raise ValueError(f"No se encontró columna de fecha. Detectamos: [{cols_found}...]. Asegúrese que la columna se llame 'fecha', 'date' o similar.")
    
    if not metadata["indices_encontrados"]:
        raise ValueError("No se reconoció ningún índice de vegetación (NDVI, NDRE, EVI, NDWI). Verifique los nombres de las columnas.")

    # Renombrar y filtrar
    df = df[list(col_map.keys())].rename(columns=col_map)
    
    # 6. Normalizar Fechas
    # Detectar heurísticamente si el formato usa '/' (típico de DD/MM/YYYY) o '-' (ISO YYYY-MM-DD)
    fechas_raw = df['fecha'].astype(str).copy()
    first_date_str = str(fechas_raw.iloc[0])
    has_slash = '/' in first_date_str
    
    try:
        if has_slash:
            # Priorizar formato latino si hay '/'
            df['fecha'] = pd.to_datetime(fechas_raw, dayfirst=True, errors='coerce')
        else:
            # Priorizar ISO/Estándar si no hay '/'
            df['fecha'] = pd.to_datetime(fechas_raw, errors='coerce')
            
        # Fallback si el método elegido falló para algunas filas (usando las fechas originales)
        mask_nat = df['fecha'].isna()
        if mask_nat.any():
            df.loc[mask_nat, 'fecha'] = pd.to_datetime(fechas_raw[mask_nat], dayfirst=not has_slash, errors='coerce')
            
    except:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

    df = df.dropna(subset=['fecha'])
    if df.empty:
        raise ValueError("No se pudieron procesar las fechas. Asegúrese de usar formatos estándar (YYYY-MM-DD o DD/MM/YYYY).")
        
    df = df.sort_values('fecha').reset_index(drop=True)
    
    # 7. Manejar NaNs e Interpolación
    for idx in metadata["indices_encontrados"]:
        # Contar NaNs
        nans = df[idx].isna().sum()
        if nans > 0:
            # Verificar si hay más de 3 consecutivos
            # (No es trivial con pandas direct, pero interpolamos y avisamos)
            df[idx] = df[idx].interpolate(method='linear', limit=3)
            still_nan = df[idx].isna().sum()
            if still_nan > 0:
                metadata["warnings"].append(f"El índice {idx} tiene demasiados datos faltantes consecutivos que no pudieron ser interpolados.")
            metadata["warnings"].append(f"Se interpolaron {nans} valores faltantes en {idx}.")

    # 8. Metadata final
    metadata["n_fechas"] = len(df)
    metadata["fecha_inicio"] = df['fecha'].min().strftime('%Y-%m-%d')
    metadata["fecha_fin"] = df['fecha'].max().strftime('%Y-%m-%d')
    
    return df, metadata
