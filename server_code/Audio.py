"""Where the lesson MP3s and transcripts live, and the short-lived links that play them.

The files sit in a PRIVATE Cloudflare R2 bucket (free storage up to 10 GB, no download fees) under the names
lessons_data gives them: en-es/L1/L1-01.mp3 and en-es/L1/L1-01.txt. Uploading: sayback/tools/upload_r2.py.
The app signs a link for one file at a time (AWS Signature V4 "presigned URL", which R2 speaks), valid for a few
hours, and only for someone allowed to hear that lesson. Nobody can list or guess the files.

Setup (App Secrets in the Anvil editor): r2_url = r2://<access key id>:<secret access key>@<account id>/<bucket>
For testing only, Admin -> Settings can set a public base address instead (anyone with a link could download).
"""
import datetime as dt
import hashlib
import hmac
import urllib.parse

from . import common as C

PLAY_HOURS = 6        # a 45-minute lesson, paused and resumed through a long day
EMPTY_HASH = "UNSIGNED-PAYLOAD"


def _secret(name):
    try:
        import anvil.secrets
        return anvil.secrets.get_secret(name) or ""
    except Exception:  # no Secrets service, or the secret isn't set yet
        return ""


def parse_r2(url):
    """'r2://KEY:SECRET@ACCOUNT/BUCKET' -> dict, or None when it doesn't look right."""
    url = (url or "").strip()
    if not url.startswith("r2://") or "@" not in url:
        return None
    cred, _, where = url[5:].rpartition("@")
    key, _, secret = cred.partition(":")
    account, _, bucket = where.partition("/")
    bucket = bucket.strip("/")
    if not (key and secret and account and bucket):
        return None
    return {"key": key, "secret": secret, "account": account, "bucket": bucket,
            "host": "%s.r2.cloudflarestorage.com" % account, "region": "auto"}


def _sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def presign(cfg, method, path, expires, when=None, query=None, service="s3"):
    """A presigned URL (AWS Signature Version 4, query-string auth). path is the URL path ('/bucket/key').
    query = extra parameters to sign (e.g. response-content-disposition). Checked against AWS's published
    example in tools/testing/test_server.py."""
    when = when or dt.datetime.now(dt.timezone.utc)
    amz_date = when.strftime("%Y%m%dT%H%M%SZ")
    day = amz_date[:8]
    scope = "%s/%s/%s/aws4_request" % (day, cfg["region"], service)
    params = dict(query or {})
    params.update({"X-Amz-Algorithm": "AWS4-HMAC-SHA256", "X-Amz-Credential": "%s/%s" % (cfg["key"], scope),
                   "X-Amz-Date": amz_date, "X-Amz-Expires": str(int(expires)), "X-Amz-SignedHeaders": "host"})
    q = lambda v: urllib.parse.quote(str(v), safe="-_.~")
    canonical_query = "&".join("%s=%s" % (q(k), q(params[k])) for k in sorted(params))
    canonical_path = urllib.parse.quote(path, safe="/-_.~")
    canonical = "\n".join([method, canonical_path, canonical_query, "host:%s\n" % cfg["host"], "host", EMPTY_HASH])
    to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical.encode("utf-8")).hexdigest()])
    k = _sign(("AWS4" + cfg["secret"]).encode("utf-8"), day)
    for part in (cfg["region"], service, "aws4_request"):
        k = _sign(k, part)
    signature = hmac.new(k, to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    return "https://%s%s?%s&X-Amz-Signature=%s" % (cfg["host"], canonical_path, canonical_query, signature)


def status():
    """How audio is set up: 'r2' (private, signed links), 'public' (a test address) or 'none'."""
    if parse_r2(_secret("r2_url")):
        return "r2"
    if public_base():
        return "public"
    return "none"


def public_base():
    base = (C.get_setting("audio_base") or "").strip()
    return base.rstrip("/") + "/" if base.startswith(("http://", "https://")) else ""


def url_for(path, download_name=None):
    """A link that plays (or, with download_name, downloads) one stored file, or None when audio isn't set up."""
    cfg = parse_r2(_secret("r2_url"))
    if cfg:
        query = {}
        if download_name:
            safe = download_name.encode("ascii", "ignore").decode() or "sayback.mp3"
            query["response-content-disposition"] = "attachment; filename=\"%s\"; filename*=UTF-8''%s" % (
                safe.replace('"', ""), urllib.parse.quote(download_name))
        return presign(cfg, "GET", "/%s/%s" % (cfg["bucket"], path), PLAY_HOURS * 3600, query=query)
    base = public_base()
    if base:
        return base + urllib.parse.quote(path)
    return None
