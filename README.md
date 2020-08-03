# ics_converter_service_component
Custom Home Assistant Component for accessing ICS Converter Service API.

Be aware that this not a plug and play component. Please note that the URL in the sensor.py must be modified!

## How to install and use
Copy the files from the custom_components folder to your Home Assistant config-folder.

Change the url in the payload to match your adress.
To find the correct url, visit the site https://ics-converter-service.dietru.de/ .

You might also need to change the names of the different waste types. For example _Hausmüll_ might be called _Restabfallbehaelter_ in your case.

Add the sensors to your configuration.yaml:

    sensor:
        - platform: ics_converter_service
          resources:
            - gelbersack
            - hausmuell
            - papiertonne
            - biotonne

## Acknowledgements
I found the code base on [Tom Beyers Blog](https://beyer-tom.de/blog/2018/11/home-assistant-integration-abfall-io-waste-collection-dates/).
There is also a thread on the [Home Assiantant Forum](https://community.home-assistant.io/t/home-assistant-integration-of-abfall-io-waste-collection-dates-schedule/80160).
