# -*- coding: utf-8 -*-
from sqlalchemy.orm.exc import NoResultFound
from pyramid_oereb.lib.records.plr import PlrRecord


def plr_tolerance_check(extract):
    """
    The function checking if the found plr results exceed the minimal surface or length
    value defined in the configuration and should therfor be represented in the extract
    or considered 'false trues' and be removed from the results.
    :param extract: The extract in it's unvalidated form
    :type extract: pyramid_oereb.lib.records.real_estate.RealEstateRecord
    """

    real_estate = extract.real_estate
    plr_records = real_estate.public_law_restrictions

    for plr_record in plr_records:
        if isinstance(plr_record, PlrRecord):
            for geometry in plr_record.geometries:
                # TODO append plr_record_geom dict to plr, rename, restructure
                geometryType = geometry.geom_type
                if geometryType == 'Point' or 'MultiPoint':
                    pass
                elif geometryType in ['Line', 'MultiLine']:
                    plr_record_geom = {
                        'type': geometryType,
                        'length': geometry.length,
                        'units': 'm'
                    }
                elif geometryType == ['Polygon', 'MultiPolygon']:
                    plr_record_geom = {
                        'type':  geometryType,
                        'area': geometry.area,
                        'area_in_percent': round(((geometry.area/real_estate.limit.area)*100), 1),
                        'units': 'm2'
                        }
                else:
                    print 'Error: unknown geometry type'
            # just for the tests:
            print plr_record_geom

    return extract


class Processor(object):

    def __init__(self, real_estate_reader, municipality_reader, plr_sources, extract_reader):
        """
        The Processor class is directly bound to the get_extract_by_id service in this application. It's task
        is to unsnarl the difficult model of the oereb extract and handle all objects inside this extract
        correctly. In addition it provides an easy to use method interface to access the information.
        It is also used to wrap all accessors in one point to have a processing interface.
        :param real_estate_reader: The real estate reader instance for runtime use.
        :type real_estate_reader: pyramid_oereb.lib.readers.real_estate.RealEstateReader
        :param municipality_reader: The municipality reader instance for runtime use.
        :type municipality_reader: pyramid_oereb.lib.readers.municipality.MunicipalityReader
        :param plr_sources: The public law restriction source instances for runtime use wrapped in a list.
        :type plr_sources: list of pyramid_oereb.lib.sources.plr.PlrStandardDatabaseSource
        :param extract_reader: The extract reader instance for runtime use.
        :type extract_reader: pyramid_oereb.lib.readers.extract.ExtractReader
        """
        self._real_estate_reader_ = real_estate_reader
        self._municipality_reader_ = municipality_reader
        self._plr_sources_ = plr_sources
        self._extract_reader_ = extract_reader

    @property
    def real_estate_reader(self):
        """

        :return: The real estate reader instance.
        :rtype real_estate_reader: pyramid_oereb.lib.readers.real_estate.RealEstateReader
        """
        return self._real_estate_reader_

    @property
    def municipality_reader(self):
        """

        :return: The municipality reader reader instance.
        :rtype municipality_reader: pyramid_oereb.lib.readers.municipality.MunicipalityReader
        """
        return self._municipality_reader_

    @property
    def plr_sources(self):
        """

        :return: The list of plr source instances.
        :rtype plr_sources: list of pyramid_oereb.lib.sources.plr.PlrStandardDatabaseSource
        """
        return self._plr_sources_

    @property
    def extract_reader(self):
        """

        :return: The extract reader instance.
        :rtype extract_reader: pyramid_oereb.lib.readers.extract.ExtractReader
        """
        return self._extract_reader_

    def process(self, real_estate):
        """
        Central processing method to hook in from webservice.
        :param real_estate: The real estate reader to obtain the real estates record.
        :type real_estate: pyramid_oereb.lib.records.real_estate.RealEstateRecord
        :return:
        """
        municipalities = self._municipality_reader_.read()
        for municipality in municipalities:
            if municipality.fosnr == real_estate.fosnr:
                if not municipality.published:
                    raise NotImplementedError
                extract_raw = self._extract_reader_.read(real_estate, municipality.logo)
                extract = plr_tolerance_check(extract_raw)
                return extract.to_extract()
        raise NoResultFound()
