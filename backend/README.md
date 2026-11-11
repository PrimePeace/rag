## 查看配置是否生效
```
python -c "from app.core.config import get_settings; get_settings.cache_clear(); print(get_settings())" 
```
显示结果：

app_name='rag-knowledge-base' log_level='INFO'

就是正确的
