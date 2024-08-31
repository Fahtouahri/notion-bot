import os
import snowflake.connector
import logging

# Configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Snowflake Configuration
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = 'xxx'
SNOWFLAKE_DATABASE = 'RAW'
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")

def get_snowflake_connection():
    logging.info("Establishing connection to Snowflake...")
    # Establishing a connection to Snowflake using environment variables and other configuration details
    return snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        role=SNOWFLAKE_ROLE,
        authenticator='externalbrowser'
    )

def execute_query(conn):
    # Query to be executed on the Snowflake database
    query = """
SELECT
   *
FROM
    notion_table 
    """
    logging.info("Executing Snowflake query...")
    # Executing the query and fetching the results
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [col[0] for col in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
    logging.info(f"Query executed. Retrieved {len(results)} rows.")
    return results

def execute_query_recommandation(conn):
    # Query for fetching recommendations from the Snowflake database
    query = """
    *
    FROM
        notion
    """
    logging.info("Executing Snowflake query for recommendations...")
    # Executing the query and fetching the results
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [col[0] for col in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
    logging.info(f"Query executed. Retrieved {len(results)} recommendations.")
    
    # Log the first few results for debugging
    for i, result in enumerate(results[:5]):
        logging.info(f"Sample result {i+1}: {result}")
    
    return results

if __name__ == "__main__":
    try:
        # Establishing the Snowflake connection
        conn = get_snowflake_connection()
        # Executing the main query
        results = execute_query(conn)
        logging.info(f"Total rows retrieved: {len(results)}")
        
        # Display the first 5 rows for verification
        for i, row in enumerate(results[:5]):
            logging.info(f"Row {i+1}:")
            for key, value in row.items():
                logging.info(f"  {key}: {value}")
            logging.info("---")
        
        # Execute the recommendation query
        reco_results = execute_query_recommandation(conn)
        logging.info(f"Total recommendations retrieved: {len(reco_results)}")
        
        # Display the first 5 recommendations for verification
        for i, row in enumerate(reco_results[:5]):
            logging.info(f"Recommendation {i+1}:")
            for key, value in row.items():
                logging.info(f"  {key}: {value}")
            logging.info("---")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        # Ensure the Snowflake connection is closed
        if conn:
            conn.close()
            logging.info("Snowflake connection closed.")
