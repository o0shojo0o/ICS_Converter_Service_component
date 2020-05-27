import logging
import requests
import csv
from datetime import datetime
from datetime import timedelta
import voluptuous as vol
from pprint import pprint

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_RESOURCES)
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(days=1)

SENSOR_PREFIX = 'Waste '

SENSOR_TYPES = {
    'hausmuell': ['Hausmüll', '', 'mdi:trash-can-outline'],
    'gelbersack': ['Gelber Sack', '', 'mdi:trash-can-outline'],
    'papiertonne': ['Papiertonne', '', 'mdi:trash-can-outline'],
    'biotonne': ['Bio-Tonne', '', 'mdi:trash-can-outline'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_RESOURCES, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("Setup ICS Converter Service API retriever")

    try:
        data = AbfallData()
    except requests.exceptions.HTTPError as error:
        _LOGGER.error(error)
        return False

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type not in SENSOR_TYPES:
            SENSOR_TYPES[sensor_type] = [
                sensor_type.title(), '', 'mdi:flash']

        entities.append(AbfallSensor(data, sensor_type))

    add_entities(entities)


class AbfallData(object):

    def __init__(self):
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        _LOGGER.debug("Updating ICS Converter Service dates using remote API")
        try:            
            j = requests.get("https://ics-converter-service.dietru.de/api/ConvertICStoCSV?url=https%3A%2F%2Fwww.awg-bassum.de%2Fabfallkalender.php%3Fcom%3Dexport%26slug%3Dposener_str.%2F-%2Fstuhr%2F28816%2Fbrinkum", timeout=10)

            apiRequest = j.text.split('\n')
            reader = csv.reader(apiRequest, delimiter=";")
            rowCounter = 0
            columns = None
            gelberSack = []
            restMuell = []
            papierTonne = []
            bioTonne = []

            for row in reader:
                if rowCounter == 0:
                    columns = {k:row.index(k) for k in row}
                    #_LOGGER.error(f"Kopfzeile: {row}")
                else:
                    if (row[columns["Verpackungstonne"]] != ""):                        
                        gelberSack.append(datetime.strptime(row[columns["Verpackungstonne"]], "%m/%d/%Y"))

                    if (row[columns["Restabfallbehaelter"]] != ""):
                        restMuell.append(datetime.strptime(row[columns["Restabfallbehaelter"]], "%m/%d/%Y"))

                    if (row[columns["Altpapiertonne"]] != ""):
                        papierTonne.append(datetime.strptime(row[columns["Altpapiertonne"]], "%m/%d/%Y"))
                       
                    if (row[columns["Bio-Tonne"]] != ""):                        
                        bioTonne.append(datetime.strptime(row[columns["Bio-Tonne"]], "%m/%d/%Y"))


                rowCounter = rowCounter + 1

            gelberSack.sort(key=lambda date: date)
            restMuell.sort(key=lambda date: date)
            papierTonne.sort(key=lambda date: date)
            bioTonne.sort(key=lambda date: date)

            nextDates = {}

            for nextDate in gelberSack:
                if nextDate > datetime.now():
                    nextDates["gelberSack"] = nextDate
                    break

            for nextDate in restMuell:
                if nextDate > datetime.now():
                    nextDates["restMuell"] = nextDate
                    break

            for nextDate in papierTonne:
                if nextDate > datetime.now():
                    nextDates["papierTonne"] = nextDate
                    break
                    
            for nextDate in bioTonne:
                if nextDate > datetime.now():
                    nextDates["bioTonne"] = nextDate                    
                    break
                    
            self.data = nextDates

        except requests.exceptions.RequestException as exc:
            _LOGGER.error("Error occurred while fetching data: %r", exc)
            self.data = None
            return False


class AbfallSensor(Entity):

    def __init__(self, data, sensor_type):
        self.data = data
        self.type = sensor_type
        self._name = SENSOR_PREFIX + SENSOR_TYPES[self.type][0]
        self._unit = SENSOR_TYPES[self.type][1]
        self._icon = SENSOR_TYPES[self.type][2]
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return self._unit

    @property
    def device_state_attributes(self):
        """Return attributes for the sensor."""
        return self._attributes

    def update(self):
        self.data.update()
        abfallData = self.data.data
        date = None
        try:
            if self.type == 'gelbersack':
                date = abfallData.get("gelberSack")
            elif self.type == 'hausmuell':
                date = abfallData.get("restMuell")
            elif self.type == 'papiertonne':
                date = abfallData.get("papierTonne")
            elif self.type == 'biotonne':
                date = abfallData.get("bioTonne")

            if date is not None:
                weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
                self._state = (date.date() - datetime.now().date()).days
                if self._state == 0:
                    printtext = "heute"
                elif self._state == 1:
                    printtext = "morgen"
                else:
                    printtext = 'in {} Tagen'.format(self._state)
                self._attributes['date'] = date.strftime('%d.%m.%Y')
                self._attributes['display_text'] = date.strftime('{}, %d.%m.%Y ({})').format(weekdays[date.weekday()], printtext)
                self._attributes['display_text_short'] = printtext
        except ValueError:
            self._state = None
