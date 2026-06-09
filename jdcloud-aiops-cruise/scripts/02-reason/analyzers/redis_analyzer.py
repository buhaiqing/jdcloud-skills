"""
jdcloud-aiops-cruise / analyzers / redis_analyzer.py
===================================================
Redis cache analyzer.

Discovery: Redis instances tagged with target customer.
Metrics:  memory usage, hit rate, connections, CPU (if available).
Features: detects high-memory (OOM risk), low hit rate (cache miss / penetration).
"""

import sys, os
_scripts_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
from analyzers import register
from analyzers.base_analyzer import BaseAnalyzer
from lib.jdc_client import get_tag, tag_dict


class RedisAnalyzer(BaseAnalyzer):
    service_name = "redis"
    icon = "🗄️"

    def discover(self, topology: dict) -> list:
        self.topology = topology
        customer = topology.get("customer", "")
        all_redis = topology.get("raw", {}).get("redis", [])
        self.resources = [r for r in all_redis if get_tag(r, "客户") == customer]
        return self.resources

    def query_metrics(self, client, hours: int = 6) -> dict:
        # Redis monitor metrics from JD Cloud:
        # - redis.memory.usage  (内存使用率 %)
        # - redis.hit_rate      (缓存命中率 %)
        # - redis.connections   (连接数)
        # - redis.cpu.util      (CPU %)
        redis_metrics = ["redis.memory.usage", "redis.hit_rate",
                         "redis.connections", "redis.cpu.util"]
        for r in self.resources:
            rid = r.get("cacheInstanceId")
            if not rid:
                continue
            try:
                pts = client.get_metrics_batch(rid, redis_metrics, hours=hours,
                                               region=client.region,
                                               service_code="redis")
                if pts:
                    self.metrics[rid] = pts
            except Exception:
                continue
        return self.metrics

    def analyze(self) -> list:
        self.findings = []
        for r in self.resources:
            rid = r.get("cacheInstanceId")
            name = r.get("cacheInstanceName", rid)
            mem_mb = r.get("cacheInstanceMemoryMB", 0)
            tags = tag_dict(r)

            metrics = self.metrics.get(rid, {})

            # Memory usage
            mem = metrics.get("redis.memory.usage", [])
            if mem:
                last = mem[-1][1]
                avg = sum(v for _, v in mem) / len(mem)
                if last > 85:
                    self._add_finding("critical",
                        f"内存使用率{last:.1f}% (规格{mem_mb}MB)",
                        "立即扩容或清理key", name)
                elif last > 75:
                    self._add_finding("warning",
                        f"内存使用率{last:.1f}%",
                        f"计划扩容或清理key (当前规格{mem_mb}MB, 已用{last*mem_mb/100:.0f}MB)",
                        name)

            # Memory trend (rising = OOM risk)
            if mem and len(mem) >= 6:
                first_half = sum(v for _, v in mem[:len(mem)//2]) / (len(mem)//2)
                second_half = sum(v for _, v in mem[len(mem)//2:]) / (len(mem) - len(mem)//2)
                if second_half > first_half * 1.2 and second_half > 60:
                    self._add_finding("warning",
                        f"内存使用率持续上升 ({first_half:.1f}% → {second_half:.1f}%)",
                        "检查是否有大key或内存泄漏", name)

            # Hit rate
            hr = metrics.get("redis.hit_rate", [])
            if hr:
                avg_hr = sum(v for _, v in hr) / len(hr)
                if avg_hr < 80:
                    self._add_finding("warning",
                        f"缓存命中率{avg_hr:.1f}% (<80%)",
                        "检查是否存在缓存穿透、热key过期", name)
                elif avg_hr < 90:
                    self._add_finding("info",
                        f"缓存命中率{avg_hr:.1f}%",
                        "建议关注", name)

            # Connections
            conn = metrics.get("redis.connections", [])
            if conn:
                avg_conn = sum(v for _, v in conn) / len(conn)
                if avg_conn > 9000:
                    self._add_finding("warning",
                        f"连接数{avg_conn:.0f}",
                        "检查是否有连接泄漏，考虑限制maxclients", name)

            # Eviction policy
            policy = r.get("maxmemoryPolicy", "unknown")
            if policy == "noeviction":
                self._add_finding("info",
                    f"淘汰策略: noeviction (内存满时写入会失败)",
                    "建议改用volatile-lru或allkeys-lru", name)

            # Version check
            ver = r.get("redisVersion", "")
            if ver and ver < "5.0":
                self._add_finding("info",
                    f"Redis版本{ver}偏旧",
                    "建议升级到5.0+以获得更好性能和安全性", name)

            # Environment tag
            env = tags.get("环境", "")
            if env:
                self._add_finding("info",
                    f"环境: {env}", "", name)

        return self.findings


register("redis", RedisAnalyzer)