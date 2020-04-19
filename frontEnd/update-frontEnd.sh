cd /home/WxT-QA-BOT/frontEnd
rm -f index.html
staticrypt main.html "WxT&IBM-BOT-Q@"
mv main_encrypted.html index.html
chmod 774 index.html
cp /home/WxT-QA-BOT/frontEnd/index.html /var/www/html
cp /home/WxT-QA-BOT/frontEnd/main.html /var/www/html