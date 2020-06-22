# Bot Interface

This is the source code of the bot interface. It is build using django and the webexteamssdk to allow your users to ask
for help. Questions are being first reviewed by a NLU system to try and find a matching answer before being escalated to 
a human in the support space. 

## Install

The bot offers a docker container (either available as a pre-build image from `mneiding/mango_uk_bot:latest` or via the 
`Dockerfile` included in this directory) for deployment. You will need a second container with a Postgres DB. Have a look
at the `docker-compose.yml` and the `env/BOTvariables.template` file in the parent directory to see which environment 
variables need to be set. 

## Customizing the cards

You can customize the "look and feel" of the cards that are being send by modifying the `bot/cards.py` file. April uses 
the [pyadaptivecards](https://github.com/CiscoSE/pyadaptivecards) framework to render the cards.

## Adding more classifier

In order to improve your classification you can experiment with different classifier. Have a look at `bot/classifier.py`. 
Here you will find the abstract class `BaseClassifier` that you can inherit from and that shows the structure of a 
classifier. Keep in mind that, in order to be abel to answer in real time your classifier should not take more then a few 
seconds to compare your input against all target questions. 

