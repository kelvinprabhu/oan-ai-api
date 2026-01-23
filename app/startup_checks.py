import logging
import os
import asyncio
from app.config import settings

# Configure logger
logger = logging.getLogger("app.startup")

async def verify_redis(cache_instance):
    """Verify Redis connection"""
    try:
        await cache_instance.set("health_check", "ok", ttl=60)
        test_value = await cache_instance.get("health_check")
        if test_value == "ok":
            logger.info("Redis: Connection successful")
        else:
            logger.warning("Redis: Connection issue - values not persisting correctly")
    except Exception as e:
        logger.error(f"Redis: Connection failed: {str(e)}")

async def verify_llm():
    """Verify LLM Configuration"""
    try:
        # We handle the import here to avoid circular dependencies if any, 
        # though agents.models is likely already imported by routers.
        # This also acts as a check if the module loaded correctly.
        from agents.models import LLM_PROVIDER, LLM_MODEL_NAME
        logger.info(f"LLM: Configured with Provider='{LLM_PROVIDER}', Model='{LLM_MODEL_NAME}'")
    except ImportError as e:
        logger.error(f"LLM: Failed to import configuration. Error: {e}")
    except Exception as e:
        logger.error(f"LLM: Verification failed. Error: {e}")

async def verify_marqo():
    """Verify Marqo DB connection and data existence"""
    endpoint = settings.marqo_endpoint_url
    index_name = settings.marqo_index_name or "oan-index"
    
    if not endpoint:
        logger.warning("⚠️ Marqo DB: Endpoint URL not configured (MARQO_ENDPOINT_URL missing).")
        return

    try:
        import marqo
        # Run in executor because marqo client might be synchronous
        client = marqo.Client(url=endpoint)
        
        # Check indexes - run in thread pool to avoid blocking async loop since marqo client is sync
        def _check_marqo():
            try:
                indexes = client.get_indexes()
                # Determine structure of indexes response
                # It usually returns {'results': [{'index_name': ...}, ...]}
                existing_indexes = []
                
                # Debug logging to see structure if needed
                # logger.debug(f"Marqo indexes response: {indexes}")

                if isinstance(indexes, dict) and 'results' in indexes:
                    # Normal Marqo response
                    existing_indexes = [i.get('index_name', i.get('indexName')) for i in indexes['results']]
                elif isinstance(indexes, list):
                     # Older versions or different wrapper
                     existing_indexes = []
                     for i in indexes:
                         if isinstance(i, dict):
                             existing_indexes.append(i.get('index_name', i.get('indexName')))
                         else:
                             existing_indexes.append(i)
                
                # Filter out None values just in case
                existing_indexes = [i for i in existing_indexes if i]

                if index_name in existing_indexes:
                    stats = client.index(index_name).get_stats()
                    doc_count = stats.get('numberOfDocuments', 0)
                    return True, doc_count, existing_indexes
                else:
                    return False, 0, existing_indexes
            except Exception as inner_e:
                raise inner_e

        loop = asyncio.get_event_loop()
        exists, doc_count, all_indexes = await loop.run_in_executor(None, _check_marqo)
        
        if exists:
            if doc_count > 0:
                logger.info(f"Marqo DB: Connected. Index '{index_name}' active with {doc_count} documents.")
            else:
                 logger.warning(f"Marqo DB: Connected. Index '{index_name}' exists but is EMPTY.")
        else:
            logger.warning(f"Marqo DB: Connected, but index '{index_name}' NOT FOUND. Available indexes: {all_indexes}")

    except Exception as e:
        logger.error(f"Marqo DB: Connection check failed. Error: {e}")

async def verify_nominatim():
    """Verify Nominatim (Maps) service"""
    try:
        # Import here to isolate potential import errors
        from agents.tools.maps import geocoder
        
        # We can try a simple reverse geocode
        # Use a well known location: Gateway of India, Mumbai (approx)
        test_lat, test_lon = 18.9220, 72.8347
        
        # Run synchronous call in executor
        def _test_nominatim():
            # Using the direct geocoder instance to test connectivity
            # reverse_geocode wrapper handles logging, we want raw check or use wrapper but catch output
            try:
                # We specify a timeout for the check
                start_val = geocoder.reverse((test_lat, test_lon), exactly_one=True, timeout=5)
                return start_val
            except Exception as e:
                # Log the actual exception for debugging
                logger.debug(f"Nominatim check internal error: {e}")
                raise e

        loop = asyncio.get_event_loop()
        location = await loop.run_in_executor(None, _test_nominatim)
        
        if location:
            logger.info(f"Nominatim: Service operational. Test location resolved to: {location.address.split(',')[0]}")
        else:
            logger.warning("Nominatim: Connected but returned no result for test coordinates.")
            
    except Exception as e:
        logger.error(f"Nominatim: Service check failed. Error: {e}")

async def perform_startup_checks(cache_instance):
    """Execute all startup verifications"""
    logger.info("--- Starting System Verification ---")
    
    # Run checks - some consecutively, some could be parallel but sequential is safer for logs readability
    await verify_redis(cache_instance)
    await verify_llm()
    await verify_marqo()
    await verify_nominatim()
    
    logger.info("--- System Verification Complete ---")
