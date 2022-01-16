Daemons to process data while search run is running goes here.


Installing a unite (example)

```sh
sudo cp systemd-services/python-search-executed-redis-consumer.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl start python-search-executed-redis-consumer.service
# check if it worked
sudo systemctl status python-search-executed-redis-consumer.service
# enable for next boot
sudo systemctl enable python-search-executed-redis-consumer.service
```
