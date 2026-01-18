import time
from arq.connections import ArqRedis
from app.core.config import settings

# Simple token bucket in Redis (atomic enough using LUA)
LUA_TOKEN_BUCKET = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])       -- tokens per window
local window = tonumber(ARGV[3])     -- seconds
local burst = tonumber(ARGV[4])      -- max tokens
local cost = tonumber(ARGV[5])       -- tokens to consume

local data = redis.call("HMGET", key, "tokens", "ts")
local tokens = tonumber(data[1])
local ts = tonumber(data[2])

if tokens == nil then
  tokens = burst
  ts = now
end

local delta = math.max(0, now - ts)
local refill = (delta / window) * rate
tokens = math.min(burst, tokens + refill)
ts = now

local allowed = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
end

redis.call("HMSET", key, "tokens", tokens, "ts", ts)
redis.call("EXPIRE", key, window * 2)

return allowed
"""

async def consume_global(redis: ArqRedis, cost: int = 1) -> bool:
    now = int(time.time())
    return bool(await redis.eval(
        LUA_TOKEN_BUCKET,
        keys=["rl:ai:global"],
        args=[now, settings.AI_RATE_GLOBAL_PER_MIN, 60, settings.AI_RATE_GLOBAL_PER_MIN + settings.AI_RATE_BURST, cost],
    ))

async def consume_user(redis: ArqRedis, user_id: str, cost: int = 1) -> bool:
    now = int(time.time())
    burst = settings.AI_RATE_USER_PER_MIN + settings.AI_RATE_BURST
    return bool(await redis.eval(
        LUA_TOKEN_BUCKET,
        keys=[f"rl:ai:user:{user_id}"],
        args=[now, settings.AI_RATE_USER_PER_MIN, 60, burst, cost],
    ))
