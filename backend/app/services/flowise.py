import httpx
import logging
import time
from functools import lru_cache
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class FlowiseError(Exception):
    """Raised when Flowise returns an error or is unreachable."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class FlowiseService:
    """
    Async wrapper around the Flowise Prediction REST API.

    Endpoint: POST {FLOWISE_URL}/api/v1/prediction/{CHATFLOW_ID}
    Payload:  { "question": "...", "overrideConfig": { "sessionId": "..." } }
    Response: { "text": "...", "sourceDocuments": [...] }
    """

    def __init__(self):
        s = get_settings()
        self.base_url    = s.FLOWISE_URL.rstrip('/')
        self.chatflow_id = s.FLOWISE_CHATFLOW_ID
        self.api_key     = s.FLOWISE_API_KEY
        self.timeout     = httpx.Timeout(connect=10.0, read=90.0, write=30.0, pool=10.0)

    def _headers(self) -> dict:
        h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if self.api_key:
            h['Authorization'] = f'Bearer {self.api_key}'
        return h

    def _prediction_url(self) -> str:
        if not self.chatflow_id:
            raise FlowiseError(
                'FLOWISE_CHATFLOW_ID is not configured. Set it in your .env file.',
                status_code=503,
            )
        return f'{self.base_url}/api/v1/prediction/{self.chatflow_id}'

    async def predict(self, question: str, session_id: str) -> dict:
        """
        Send question to Flowise RAG pipeline.

        Returns:
            dict with keys: 'text', 'sourceDocuments'

        Raises:
            FlowiseError on any failure
        """
        url = self._prediction_url()
        payload = {
            'question': question,
            'overrideConfig': {
                'sessionId': session_id,
            },
        }

        logger.info(f'[Flowise] POST {url}  session={session_id[:8]}…')
        t0 = time.monotonic()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers())

            elapsed = round((time.monotonic() - t0) * 1000)
            logger.info(f'[Flowise] {response.status_code} in {elapsed}ms')

            if response.status_code == 401:
                raise FlowiseError('Flowise authentication failed. Check FLOWISE_API_KEY.', 401)
            if response.status_code == 404:
                raise FlowiseError(
                    f'Chatflow not found: {self.chatflow_id}. Verify FLOWISE_CHATFLOW_ID.', 404
                )
            if response.status_code >= 400:
                try:
                    body = response.json()
                    msg  = body.get('message', response.text)
                except Exception:
                    msg = response.text
                raise FlowiseError(f'Flowise error {response.status_code}: {msg}', response.status_code)

            data = response.json()
            logger.debug(f'[Flowise] Response keys: {list(data.keys())}')
            return data

        except httpx.TimeoutException as exc:
            logger.error(f'[Flowise] Timeout after {round(time.monotonic()-t0)}s: {exc}')
            raise FlowiseError(
                'Flowise request timed out after 90 seconds. The model may be warming up — try again.',
                status_code=504,
            )
        except httpx.ConnectError as exc:
            logger.error(f'[Flowise] Connection error: {exc}')
            raise FlowiseError(
                f'Cannot connect to Flowise at {self.base_url}. Is it running?',
                status_code=503,
            )
        except FlowiseError:
            raise
        except Exception as exc:
            logger.error(f'[Flowise] Unexpected error: {exc}', exc_info=True)
            raise FlowiseError(f'Unexpected Flowise error: {str(exc)}', status_code=502)

    async def health(self) -> str:
        """Ping Flowise health endpoint."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                r = await client.get(f'{self.base_url}/api/v1/ping', headers=self._headers())
            return 'ok' if r.status_code == 200 else f'http_{r.status_code}'
        except Exception as exc:
            logger.warning(f'[Flowise] Health failed: {exc}')
            return 'unreachable'


@lru_cache
def get_flowise_service() -> FlowiseService:
    return FlowiseService()
