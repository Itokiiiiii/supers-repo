from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt
import io

app = FastAPI()

# conexión a la base de datos 
DATABASE_URL = "mysql+pymysql://root:rootpassword@mysql:3306/superhero"
engine = create_engine(DATABASE_URL)


from fastapi import Query

@app.get("/grafico", tags=["Graficos"])
def superheroes_con_mas_superpoderes(top: int = Query(20, ge=1, le=100)):
    # 1. Leer datos
    df_superhero = pd.read_sql_query("SELECT * FROM superhero", engine)
    df_hero_power = pd.read_sql_query("SELECT * FROM hero_power", engine)
    df_superpower = pd.read_sql_query("SELECT * FROM superpower", engine)

    # 2. Hacer los joins
    merged = pd.merge(df_superhero, df_hero_power, left_on='id', right_on='hero_id')
    final = pd.merge(merged, df_superpower, left_on='power_id', right_on='id')

    # 3. Agrupar por superhéroe y contar superpoderes
    poderes_por_heroe = final.groupby('superhero_name').count()['power_name']
    poderes_por_heroe = poderes_por_heroe.sort_values(ascending=False)

    # 4. Crear el gráfico con el top deseado
    fig, ax = plt.subplots(figsize=(12, 6))
    poderes_por_heroe.head(top).plot(kind='bar', ax=ax, color='red')
    plt.title(f'Top {top} Superhéroes con más superpoderes')
    plt.xlabel('Superhéroe')
    plt.ylabel('Cantidad de Superpoderes')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # 5. Guardarlo en memoria
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return StreamingResponse(buf, media_type="image/png")


@app.get("/grafico-genero", tags=["Graficos"])
def genero_por_superheroes():
    try:
        df_superhero = pd.read_sql_query("SELECT * FROM superhero", engine)
        df_genero = pd.read_sql_query("SELECT * FROM gender", engine)

        merged = pd.merge(df_superhero, df_genero, left_on="gender_id", right_on="id")

        conteo = merged["gender"].value_counts()

        fig, ax = plt.subplots(figsize=(8, 6))
        conteo.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90, legend=False)
        plt.title("Género entre Superhéroes")
        plt.ylabel("")  

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)

        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        print("❌ Error en grafico-genero:", str(e))
        return {"error": str(e)}



from fastapi import Query

@app.get("/top-poder", tags=["Graficos"])
def top_superheroes_mas_cabrones_de_todos(top: int = Query(10, ge=1, le=100)):
    try:
        
        df_superhero = pd.read_sql_query("SELECT id, superhero_name FROM superhero", engine)
        df_hero_attribute = pd.read_sql_query("SELECT * FROM hero_attribute", engine)
        df_attribute = pd.read_sql_query("SELECT * FROM attribute", engine)

        merged = pd.merge(df_hero_attribute, df_attribute, left_on="attribute_id", right_on="id")

        pivot = merged.pivot_table(index="hero_id", 
                                   columns="attribute_name", 
                                   values="attribute_value")

        pivot = pivot.fillna(0)
        pivot["poder_total"] = pivot.sum(axis=1)

        resultado = pd.merge(pivot, df_superhero, left_index=True, right_on="id")

        top_resultado = resultado[["superhero_name", "poder_total"]]\
                          .sort_values(by="poder_total", ascending=False)\
                          .head(top)

        fig, ax = plt.subplots(figsize=(15, 6))
        top_resultado.set_index("superhero_name")["poder_total"].plot(kind="bar", color="purple", ax=ax)
        plt.title(f"Top {top} Superhéroes más cabrones")
        plt.ylabel("Poder Total")
        plt.xlabel("Superhéroe")
        plt.xticks(rotation=45)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)

        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        print("Error en /top-poder:", str(e))
        return {"error": str(e)}




    
    
@app.get("/superheroes", tags=["Tablas"])
def lista_de_superheroes():
    try:
        df = pd.read_sql_query("SELECT * FROM superhero", engine)
        df = df.fillna(0)  #convierte NaN a 0
        df = df.replace([float('inf'), float('-inf')], 0)  #elimina infinitos
        return df.to_dict(orient="records")
    except Exception as e:
        print("❌ Error en /superheroes:", str(e))
        raise e

@app.get("/razas", tags=["Tablas"])
def tipos_de_raza():
    try:
        query = """
        SELECT race.race, COUNT(*) AS count
        FROM superhero
        JOIN race ON superhero.race_id = race.id
        GROUP BY race.race
        ORDER BY count DESC;
        """
        df = pd.read_sql_query(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        print("Error al consultar razas:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
        
        
@app.get("/editoriales", tags=["Tablas"])
def editoriales_de_comics():
    try:
        query = """
        SELECT publisher.publisher_name AS editorial, COUNT(*) AS cantidad
        FROM superhero
        JOIN publisher ON superhero.publisher_id = publisher.id
        GROUP BY publisher.publisher_name
        ORDER BY cantidad DESC;
        """
        df = pd.read_sql_query(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        print("Error al consultar editoriales:", str(e))
        return {"error": str(e)}



from fastapi import Query

@app.get("/superheroes-altos", tags=["Consultas"])
def superheroes_mas_altos(altura_min: float = Query(300, ge=0, description="altura mínima en cm")):
    try:
        query = f"""
            SELECT superhero_name, height_cm
            FROM superhero
            WHERE height_cm > {altura_min}
            ORDER BY height_cm DESC
        """
        df = pd.read_sql_query(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        print("Error en /superheroes-altos:", str(e))
        return {"error": str(e)}


@app.get("/top-poder-dc", tags=["Consultas"])
def superheroes_mas_poderosos_de_DC_comics(top: int = Query(10, ge=1, le=100)):
    try:
        query = f"""
        SELECT s.superhero_name, SUM(ha.attribute_value) AS poder_total
        FROM superhero s
        JOIN hero_attribute ha ON s.id = ha.hero_id
        JOIN publisher p ON s.publisher_id = p.id
        WHERE p.publisher_name = 'DC Comics'
        GROUP BY s.superhero_name
        ORDER BY poder_total DESC
        LIMIT {top}
        """
        df = pd.read_sql_query(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        print("Error en /top-dc:", str(e))
        return {"error": str(e)}


@app.get("/top-poder-image", tags=["Consultas"])
def superheroes_mas_poderosos_de_image_comics(top: int = Query(10, ge=1, le=100)):
    try:
        query = f"""
        SELECT s.superhero_name, SUM(ha.attribute_value) AS poder_total
        FROM superhero s
        JOIN hero_attribute ha ON s.id = ha.hero_id
        JOIN publisher p ON s.publisher_id = p.id
        WHERE p.publisher_name = 'Image Comics'
        GROUP BY s.superhero_name
        ORDER BY poder_total DESC
        LIMIT {top}
        """
        df = pd.read_sql_query(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        print("Error en /top-image:", str(e))
        return {"error": str(e)}


@app.get("/razas-mas-poderosas", tags=["Consultas"])
def razas_con_mas_poderes():
    try:
        query = """
        SELECT r.race, COUNT(*) AS cantidad_poderes
        FROM hero_power hp
        JOIN superhero s ON hp.hero_id = s.id
        JOIN race r ON s.race_id = r.id
        WHERE r.race IS NOT NULL
        GROUP BY r.race
        ORDER BY cantidad_poderes DESC
        """
        df = pd.read_sql_query(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        print("Error en /razas-mas-poderosas:", str(e))
        return {"error": str(e)}

@app.get("/superheroes-mas-inteligentes", tags=["Consultas"])
def superheroes_mas_inteligentes():
    try:
        query = """
        SELECT s.superhero_name, ha.attribute_value AS inteligencia
        FROM superhero s
        JOIN hero_attribute ha ON s.id = ha.hero_id
        JOIN attribute a ON ha.attribute_id = a.id
        WHERE a.attribute_name = 'Intelligence'
        ORDER BY ha.attribute_value DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        print("Error en /superheroes-inteligentes:", str(e))
        return {"error": str(e)}

@app.get("/poderes-comunes", tags=["Consultas"])
def superpoderes_mas_comunes():
    try:
        query = """
        SELECT sp.power_name, COUNT(*) AS cantidad
        FROM hero_power hp
        JOIN superpower sp ON hp.power_id = sp.id
        GROUP BY sp.power_name
        ORDER BY cantidad DESC
        LIMIT 20;
        """
        df = pd.read_sql_query(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        print("Error en /poderes-comunes:", str(e))
        return {"error": str(e)}

