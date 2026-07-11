import time, psycopg2
print("Application Python démarrée...")
conn_str = "host=db_service user=postgres password=secret dbname=test_db"
while True:
    try:
        conn = psycopg2.connect(conn_str)
        print("✅ Connexion réussie à PostgreSQL depuis le conteneur Python !")
        conn.close()
        break
    except psycopg2.OperationalError:
        print("⏳ BDD non prête, réessai dans 2 secondes...")
        time.sleep(2)