# 尝试启动，如果因为已存在而报错，则进行重启
pm2 start ecosystem.config.js || pm2 restart ecosystem.config.js
pm2 save