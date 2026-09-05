"""
Keepalive para Neo4j AuraDB Free.

AuraDB Free pausa la instancia tras 72h sin actividad y la elimina tras
30 días de inactividad. Este script corre una consulta trivial para que
siempre haya actividad reciente. Pensado para ejecutarse desde GitHub
Actions con cron semanal (ver .github/workflows/neo4j_keepalive.yml).

Requiere las variables de entorno: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
"""
import os
import sys
from neo4j import GraphDatabase


def main() -> int:
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS total")
            total = result.single()["total"]
            print(f"Keepalive OK — {total} nodos en la base. Instancia activa.")
        return 0
    except Exception as e:
        print(f"Keepalive FALLÓ: {e}", file=sys.stderr)
        return 1
    finally:
        driver.close()


if __name__ == "__main__":
    sys.exit(main())
