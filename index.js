const express = require("express");
const { Etcd3 } = require("etcd3");
const { LRUCache } = require("lru-cache");
const fs = require("fs");

const app = express();
app.use(express.json());

// Cache Configuration
const cache = new LRUCache({
  max: 500, // Maximum number of items
  ttl: 1000 * 60, // 1 minute TTL
});

// Configuration
const etcdHosts = process.env.ETCD_HOSTS
  ? process.env.ETCD_HOSTS.split(",")
  : [
      "http://100.101.75.66:2379",
      "http://100.111.100.103:2379",
      "http://100.123.53.56:2379",
    ];

const etcdAuth = {
  username: process.env.ETCD_USERNAME || "",
  password: process.env.ETCD_PASSWORD || "",
};

const grpcOptions = {};
if (process.env.ETCD_CA_CERT) {
  grpcOptions["ssl-target-name-override"] = "etcd"; // default for testing
  // grpcOptions.checkServerIdentity = () => undefined; // for self-signed
  // Load certs if paths provided
  // ... (simplified for now as placeholder)
}

// 连接 etcd
const etcdOptions = {
  hosts: etcdHosts,
  auth: etcdAuth.username ? etcdAuth : undefined,
  grpcOptions,
};

let etcd;

try {
  etcd = new Etcd3(etcdOptions);
} catch (error) {
  console.error("Failed to initialize Etcd client:", error);
}

// Health check / Connection test
const checkEtcdConnection = async () => {
  if (!etcd) return false;
  try {
    // Try to get a dummy key or root
    await etcd.get("health_check").string();
    return true;
  } catch (err) {
    console.error("Etcd connection error:", err.message);
    return false;
  }
};

// Middleware to check etcd availability
const ensureEtcd = async (req, res, next) => {
  if (!etcd) {
    return res.status(503).json({ error: "Etcd client not initialized" });
  }
  // Optional: Check connectivity on every request or rely on client's internal retry
  // For high performance, rely on client. For strict availability, check.
  // We'll rely on client but catch errors in routes.
  next();
};

// 🔹 获取 key
app.get("/kv/:key", ensureEtcd, async (req, res) => {
  try {
    const decodedKey = decodeURIComponent(req.params.key);

    // Check cache first
    if (cache.has(decodedKey)) {
      return res.json({ key: req.params.key, value: cache.get(decodedKey), cached: true });
    }

    // Add timeout or fallback
    const value = await etcd.get(decodedKey).string();
    if (value === null) return res.status(404).json({ error: "Key not found" });

    // Update cache
    cache.set(decodedKey, value);

    res.json({ key: req.params.key, value });
  } catch (err) {
    console.error("Error getting key:", err);
    res.status(503).json({ error: "Etcd service unavailable or error", details: err.message });
  }
});

// 🔹 新增或更新 key
app.post("/kv", ensureEtcd, async (req, res) => {
  const { key, value } = req.body;
  if (!key || value === undefined) return res.status(400).json({ error: "Key and value required" });
  try {
    await etcd.put(key).value(value);
    // Invalidate cache
    cache.delete(key);
    res.json({ success: true });
  } catch (err) {
    console.error("Error putting key:", err);
    res.status(503).json({ error: "Etcd service unavailable or error", details: err.message });
  }
});

// 🔹 删除 key
app.delete("/kv/:key", ensureEtcd, async (req, res) => {
  try {
    const decodedKey = decodeURIComponent(req.params.key);
    await etcd.delete().key(decodedKey);
    // Invalidate cache
    cache.delete(decodedKey);
    res.json({ success: true });
  } catch (err) {
    console.error("Error deleting key:", err);
    res.status(503).json({ error: "Etcd service unavailable or error", details: err.message });
  }
});

// 🔹 列出所有 key（可选）
app.get("/kv", ensureEtcd, async (req, res) => {
  try {
    const all = await etcd.getAll().strings();
    res.json(all);
  } catch (err) {
    console.error("Error listing keys:", err);
    res.status(503).json({ error: "Etcd service unavailable or error", details: err.message });
  }
});

app.listen(5001, () => {
  console.log("✅ etcd API server running on http://localhost:5001");
});
