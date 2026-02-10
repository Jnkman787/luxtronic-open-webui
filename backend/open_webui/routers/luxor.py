import logging
import aiohttp
import os
import json
from typing import Optional, Union
from fastapi import (
    HTTPException,
)
from open_webui.env import (
    SRC_LOG_LEVELS,
    AIOHTTP_CLIENT_SESSION_SSL,
    AIOHTTP_CLIENT_TIMEOUT,
)
from open_webui.models.users import UserModel
from open_webui.utils.payload import _build_user_jwt_token

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

async def rag_master_request(form_data: dict, user: Optional[UserModel] = None):
    url = os.environ.get("RAG_PLATFORM_URL")
    if not url:
        raise HTTPException(
            status_code=500,
            detail="Missing RAG_PLATFORM_URL environment variable",
        )
    return await send_post_request(
        url=url,
        payload=json.dumps(form_data),
        user=user,
    )

# CGH TODO Support Streaming
async def send_post_request(
        url: str,
        payload: Union[str, bytes],
        user: Optional[UserModel] = None,
):
    r = None
    try:
        # Ensure jwt_token is present in the payload if user is provided
        if user:
            try:
                payload_str = payload.decode("utf-8") if isinstance(payload, bytes) else payload
                payload_dict = json.loads(payload_str)
                if "jwt_token" not in payload_dict:
                    payload_dict["jwt_token"] = _build_user_jwt_token(user)
                    payload = json.dumps(payload_dict)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                log.warning(f"Could not inject jwt_token into payload: {e}")

        session = aiohttp.ClientSession(
            trust_env=True, timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT)
        )
        api_key = os.environ.get("RAG_MASTER_API_KEY", "")
        log_payload = payload.decode("utf-8", errors="replace") if isinstance(payload, bytes) else payload
        log.info(f"LUXOR POST payload: {log_payload}")
        r = await session.post(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
            },
            ssl=AIOHTTP_CLIENT_SESSION_SSL,
        )
        # CGH Todo remove code accounting for lack of aws gateway
        if r.ok is False:
            try:
                error_text = await r.text()
                log.error(
                    f"Luxor request failed status={r.status} url={url} body={error_text}"
                )
                res = json.loads(error_text) if error_text else {}
                await cleanup_response(r, session)
                if "error" in res:
                    raise HTTPException(status_code=r.status, detail=res["error"])
            except HTTPException as e:
                raise e  # Re-raise HTTPException to be handled by FastAPI
            except Exception as e:
                log.error(f"Failed to parse error response: {e}")
                raise HTTPException(
                    status_code=r.status,
                    detail=f"Open WebUI: Server Connection Error",
                )
            
        raw_body = await r.text()

        log.info(f"RAW BODY: {raw_body}")

        r.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)\
        
        try:
            res = json.loads(raw_body)  # works when Lambda returns JSON
            log.info("LAMBDA")
        except json.JSONDecodeError:
            log.info("DOCKER")
            res = {"statusCode": r.status, "body": raw_body}

        log.info(f"RES: {res}")
        if isinstance(res, dict) and "body" in res:
            body = res["body"]
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    body = {"txt_answer": body}
            elif not isinstance(body, dict):
                body = {"txt_answer": str(body)}

            res["data"] = body 
            
        return res      
    except HTTPException as e:
        raise e  # Re-raise HTTPException to be handled by FastAPI
    except Exception as e:
        detail = f"Luxor: {e}"

        raise HTTPException(
            status_code=r.status if r else 500,
            detail=detail if e else "Open WebUI: Server Connection Error",
        )
    finally:
        await cleanup_response(r, session)


async def cleanup_response(
    response: Optional[aiohttp.ClientResponse],
    session: Optional[aiohttp.ClientSession],
):
    if response:
        response.close()
    if session:
        await session.close()

    


    
    
