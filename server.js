const express = require("express");
const { Etcd3 } = require("etcd3");

const app = express();
app.use(express.json());

// 连接 etcd
const etcd = new Etcd3({ hosts: "http://localhost:2379" });

// 🔹 获取 key
app.get("/kv/:key", async (req, res) => {
  try {
    const decodedKey = decodeURIComponent(req.params.key);
    const value = await etcd.get(decodedKey).string();
    if (value === null) return res.status(404).json({ error: "Key not found" });
    res.json({ key: req.params.key, value });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 🔹 新增或更新 key
app.post("/kv", async (req, res) => {
  const { key, value } = req.body;
  if (!key || value === undefined) return res.status(400).json({ error: "Key and value required" });
  try {
    await etcd.put(key).value(value);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 🔹 删除 key
app.delete("/kv/:key", async (req, res) => {
  try {
    const decodedKey = decodeURIComponent(req.params.key);
    await etcd.delete().key(decodedKey);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 🔹 列出所有 key（可选）
app.get("/kv", async (req, res) => {
  try {
    const all = await etcd.getAll().strings();
    res.json(all);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(5001, () => {
  console.log("✅ etcd API server running on http://localhost:5001");
});
