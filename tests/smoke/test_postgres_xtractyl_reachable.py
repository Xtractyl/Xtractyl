import psycopg2


def test_postgres_xtractyl_reachable(
    postgres_xtractyl_host,
    postgres_xtractyl_port,
    postgres_xtractyl_db,
    postgres_xtractyl_user,
    postgres_xtractyl_password,
):
    conn = psycopg2.connect(
        host=postgres_xtractyl_host,
        port=postgres_xtractyl_port,
        dbname=postgres_xtractyl_db,
        user=postgres_xtractyl_user,
        password=postgres_xtractyl_password,
        connect_timeout=5,
    )
    conn.close()