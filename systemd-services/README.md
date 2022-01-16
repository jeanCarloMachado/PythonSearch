Daemons to process data while search run is running goes here.


Installation

```sh
sudo cp systemd-services/python-search-executed-redis-consumer.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl start python-search-executed-redis-consumer.service
sudo systemctl status python-search-executed-redis-consumer.service
sudo systemctl enable python-search-executed-redis-consumer.service
```
