from datetime import date, datetime, time

from apify import Actor

from .input_model import DatasetQueryAgent as ActorInput


async def check_inputs(actor_input: ActorInput, payload: dict) -> ActorInput:
    """Check that provided input exists"""

    resource = payload.get('payload', {}).get('resource', {})
    dataset_id = resource.get('defaultDatasetId') or actor_input.datasetId or ''

    if not dataset_id:
        msg = (
            "The Apify's `datasetId` is not provided. "
            'There are two ways to specify the `datasetId` or `keyValueStoreId`: '
            '1. Automatic Input: If this Actor is used with other Actors, the variables should be '
            "automatically passed in the 'payload'. Please check the `Input` payload to ensure that they are included."
            "2. Manual Input: If you are running this Actor independently, you can to manually specify the 'datasetId'"
            'Please verify that one of these options is correctly configured.'
        )
        Actor.log.error(msg)
        await Actor.fail(status_message=msg)

    actor_input.datasetId = dataset_id
    return actor_input


def get_python_type(sql_type: str) -> type:
    """
    Map common SQL types to Python types.

    If the type indicates an array (ends with "[]"), recursively map its element type
    and return a `list` of that type.

    :param sql_type: A string containing the SQL type (e.g., "VARCHAR", "TINYINT", "INTEGER[]").
    :return: A Python type corresponding to the given SQL type.
    """
    sql_type = sql_type.strip().upper()

    # Handle SQL array types (e.g., INTEGER[] -> list[int])
    if sql_type.endswith('[]'):
        return list

    # Map common SQL types to Python types.
    sql_type_mappings = {
        'VARCHAR': str,
        'CHAR': str,
        'TEXT': str,
        'TINYINT': int,  # Often a shortcut for an integer
        'SMALLINT': int,
        'BIGINT': int,
        'INT': int,
        'DOUBLE': float,
        'FLOAT': float,
        'DECIMAL': float,
        'NUMERIC': float,
        'BOOLEAN': bool,
        'BIT': bool,
        'DATE': date,
        'DATETIME': datetime,
        'TIMESTAMP': datetime,
        'TIME': time,
        'BLOB': bytes,
        'BINARY': bytes,
        'JSON': dict,
    }

    # Handle tinyint special cases (e.g., TINYINT(1)).
    if sql_type.startswith('TINYINT') and '(1)' in sql_type:
        return bool

    # Provide a fallback to `str` if the type is unrecognized.
    return sql_type_mappings.get(sql_type, str)



