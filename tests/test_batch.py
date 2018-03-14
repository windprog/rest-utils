#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/3/7
Desc    :   
"""
from sqlalchemy.orm import relationship, backref
from base import ChinookMemoryManagerTestBase, SqliteManagerTestBase, loads, dumps


class CollectionKeyAttributeTestCase(ChinookMemoryManagerTestBase):
    def setUp(self):
        super(CollectionKeyAttributeTestCase, self).setUp()
        self.manager.add(self.Track, methods=['GET', 'POST', "PUT", "DELETE"], key_field="Name")
        self.manager.add(self.Playlist, methods=['GET', 'POST', "PUT", "DELETE"], key_field="Name")

        res = self.put('/Track/@CollectionKeyAttributeTestCase_name', json={
            u'AlbumId': 1,
            u'Bytes': 11170334,
            u'Composer': u'Angus Young, Malcolm Young, Brian Johnson',
            u'Genre': {
                u'GenreId': 1,
                u'Name': u'Rock'
            },
            u'GenreId': 1,
            u'MediaType': {
                u'MediaTypeId': 1,
                u'Name': u'MPEG audio file'
            },
            u'MediaTypeId': 1,
            u'Milliseconds': 343719,
            u'Name': u'CollectionKeyAttributeTestCase_name',
            u'UnitPrice': u'0.99',
            u'PlaylistCollection': [
                {
                    u'PlaylistId': 1,
                    u'Name': u'Music'
                },
                {
                    u'PlaylistId': 17,
                    u'Name': u'Heavy Metal Classic'
                },
                {
                    u'PlaylistId': 12,
                    u'Name': u'Classical'
                },
            ],
        })
        assert res.status_code == 201

    def test_get_sub_collection_and_data_not_change(self):
        """
        测试获取子资源,并且确认子资源未更改
        :return:
        """
        result = loads(self.get('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection').data)
        assert len(result['items']) == result['total'] == 3
        self.assertListItemEqual(result['items'], [
            {
                u'PlaylistId': 1,
                u'Name': u'Music'
            },
            {
                u'PlaylistId': 17,
                u'Name': u'Heavy Metal Classic'
            },
            {
                u'PlaylistId': 12,
                u'Name': u'Classical'
            },
        ])

    def test_get_error(self):
        res = self.get('/Track/@CollectionKeyAttributeTestCase_name/NotFound')
        assert res.status_code == 404
        # self.assertRestException(res, "ResourceRelationNotExists")  # 变为默认页面了

    def test_get_obj(self):
        result = self.get('/Track/@CollectionKeyAttributeTestCase_name/MediaType').json()
        assert result == {
            u'MediaTypeId': 1,
            u'Name': u'MPEG audio file'
        }

    def test_post_not_found(self):
        res = self.post('/Track/@CollectionKeyAttributeTestCase_name/NotFound', json={
            u'Name': u"On-The-Go 1",
            u'PlaylistId': 18
        })
        assert res.status_code == 404
        # self.assertRestException(res, "ResourceRelationNotExists")  # 变为默认页面了

    def test_post_not_relationships(self):
        res = self.post('/Track/@CollectionKeyAttributeTestCase_name/Bytes', json={
            u'Bytes': 112233,
        })
        assert res.status_code == 404
        # self.assertRestException(res, "ResourceRelationNotExists")  # 变为默认页面了

    def test_post_add_sub_resource(self):
        res = self.post('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection', json={
            u'Name': u"On-The-Go 1",
            u'PlaylistId': 18
        })
        assert res.status_code == 200
        assert res.json()[-1] == {
            u'Name': u"On-The-Go 1",
            u'PlaylistId': 18
        }
        assert len(res.json()) == 1

    def test_post_add_sub_collection(self):
        p_res = self.post('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection', json=[{
            u'Name': u"On-The-Go 1",
            u'PlaylistId': 18
        }, {
            u'Name': u"Heavy Metal Classic",
            u'PlaylistId': 17
        }, {
            u'Name': u"Heavy Metal Classic",  # 传入多个一样的,取最后一个为准
            u'PlaylistId': 17
        }, {
            u'Name': u'Classical 101 - Deep Cuts',
            u'PlaylistId': 13
        }
        ])
        assert p_res.status_code == 200
        res = self.get('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection')
        assert res.status_code == 200
        # 注意:资源没有顺序可言
        self.assertListItemEqual(res.json()["items"], [
            {
                u'Name': u"On-The-Go 1",
                u'PlaylistId': 18
            },
            {
                u'Name': u"Classical 101 - Deep Cuts",
                u'PlaylistId': 13
            },
            {
                u'Name': u"Heavy Metal Classic",
                u'PlaylistId': 17
            }
        ])

    def test_put_sub_collection(self):
        # 替换关系成功
        res = self.put('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection', json=[{
            u'Name': u"On-The-Go 1",
            u'PlaylistId': 18
        }, {
            u'Name': u"Heavy Metal Classic",
            u'PlaylistId': 17
        }, {
            u'Name': u'Classical 101 - Deep Cuts',
            u'PlaylistId': 13
        }
        ])
        assert res.status_code == 200
        self.assertListItemEqual(res.json(), [
            {
                u'Name': u'Heavy Metal Classic',
                u'PlaylistId': 17
            },
            {
                u'Name': u'On-The-Go 1',
                u'PlaylistId': 18
            },
            {
                u'Name': u'Classical 101 - Deep Cuts',
                u'PlaylistId': 13
            }
        ])

    def test_put_not_relationships(self):
        # 替换关系不成功
        res = self.put('/Track/@CollectionKeyAttributeTestCase_name/Bytes', json={
            u'Bytes': 112233,
        })
        assert res.status_code == 404
        # self.assertRestException(res, "ResourceRelationNotExists")  # 变为默认页面了

    def test_put_not_list_relationships(self):
        # 替换关系不成功, 字典关系不能用列表替换
        res = self.put('/Track/@CollectionKeyAttributeTestCase_name/Genre', json=[{
            u'GenreId': 2
        }])
        assert res.status_code == 400
        self.assertRestException(res, "IllegalRequestData")

    def test_delete_not_found(self):
        res = self.delete('/Track/@CollectionKeyAttributeTestCase_name/NotFound', json={
            u'Name': u'Heavy Metal Classic',
            u'PlaylistId': 17,
        })
        assert res.status_code == 404
        # self.assertRestException(res, "ResourceRelationNotExists")  # 变为默认页面了
        self.test_get_sub_collection_and_data_not_change()  # 删除不成功

    def test_delete_not_relationships(self):
        res = self.delete('/Track/@CollectionKeyAttributeTestCase_name/Bytes', json={
            u'Name': u'Heavy Metal Classic',
            u'PlaylistId': 17,
        })
        assert res.status_code == 404
        # self.assertRestException(res, "ResourceRelationNotExists")  # 变为默认页面了
        self.test_get_sub_collection_and_data_not_change()  # 删除不成功

    def test_delete_not_exist_sub_resource(self):
        """
        删除一个不存在的子资源
        :return:
        """
        new_playlist = self.post("/Playlist", json={
            u"Name": u"Grunge"
        })
        res = self.delete('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection', json={
            u'PlaylistId': new_playlist.json()[u"PlaylistId"],
        })
        assert res.status_code == 404
        self.assertRestException(res, "ResourceRelationNotExists")
        self.test_get_sub_collection_and_data_not_change()  # 删除不成功

    def test_delete_sub_resource(self):
        res = self.delete('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection', json={
            u'Name': u'Heavy Metal Classic',
            u'PlaylistId': 17,
        })
        assert res.status_code == 204
        result = self.get('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection').json()
        assert result['total'] == len(result['items']) == 2
        self.assertListItemEqual(result['items'], [
            {
                u'PlaylistId': 1,
                u'Name': u'Music'
            },
            {
                u'PlaylistId': 12,
                u'Name': u'Classical'
            }
        ])

    def test_delete_sub_collection(self):
        res = self.delete('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection', json=[
            {
                u'PlaylistId': 1,
            },
            {
                u'PlaylistId': 17,
            },
            {
                u'PlaylistId': 12,
            },
        ])
        assert res.status_code == 204
        assert self.get('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection').json() == {
            u'items': [],
            u'total': 0
        }

    def test_delete_not_collection_resource(self):
        res = self.delete('/Track/@CollectionKeyAttributeTestCase_name/Genre', json={
            u'GenreId': 1,
            u'Name': u'Rock'
        })
        assert res.status_code == 204
        assert self.get('/Track/@CollectionKeyAttributeTestCase_name/Genre').json() == {}

    def test_delete_all_and_add(self):
        self.test_delete_sub_collection()
        res = self.post('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection', json=[
            {
                u'PlaylistId': 1,
            },
            {
                u'PlaylistId': 17,
            },
            {
                u'PlaylistId': 12,
            },
        ])
        self.test_get_sub_collection_and_data_not_change()

    def test_get_with_params(self):
        res = self.get('/Track/@CollectionKeyAttributeTestCase_name/PlaylistCollection', params={
            "PlaylistId": 1,
        })
        assert res.status_code == 200
        assert res.json()['items'] == [
            {
                u'PlaylistId': 1,
                u'Name': u'Music'
            },
        ]


class CollectionKeyTestCase(ChinookMemoryManagerTestBase):
    def setUp(self):
        super(CollectionKeyTestCase, self).setUp()
        self.manager.add(self.Track, methods=['GET', 'POST', "PUT", "DELETE"], key_field="Name")
        self.manager.add(self.Playlist, methods=['GET', 'POST', "PUT", "DELETE"], key_field="Name")
        self.manager.add(self.MediaType, methods=['GET', 'POST', "PUT", "DELETE"], key_field="Name")
        self.manager.add(self.Artist, methods=['GET', 'POST', "PUT", "DELETE"], key_field="Name")
        self.manager.add(self.Album, methods=['GET', 'POST', "PUT", "DELETE"], key_field="Name")

        # 创建
        res = self.post('/Track/@CollectionKeyTestCase_name', json={
            u'AlbumId': 1,
            u'Bytes': 11170334,
            u'Composer': u'Angus Young, Malcolm Young, Brian Johnson',
            u'Genre': {
                u'GenreId': 1,
                u'Name': u'Rock'
            },
            u'GenreId': 1,
            u'MediaType': {
                u'MediaTypeId': 1,
                u'Name': u'MPEG audio file'
            },
            u'MediaTypeId': 1,
            u'Milliseconds': 343719,
            u'Name': u'CollectionKeyTestCase_name',
            u'UnitPrice': u'0.99',
            u'PlaylistCollection': [
                {
                    u'PlaylistId': 1,
                    u'Name': u'Music'
                },
                {
                    u'PlaylistId': 17,
                    u'Name': u'Heavy Metal Classic'
                },
                {
                    u'PlaylistId': 12,
                    u'Name': u'Classical'
                },
            ],
        })
        assert res.status_code == 201

        res = self.post("/Artist", json={
            "Name": "ExistArtist",
        })
        assert res.status_code == 201
        self.exist_artist_id = res.json()["ArtistId"]

    def tearDown(self):
        assert self.delete('/Track/@CollectionKeyTestCase_name').status_code == 204

    def get_track(self):
        res = self.get('/Track/@CollectionKeyTestCase_name')
        assert res.status_code == 200
        return res.json()

    def test_create_exist_resource(self):
        exists_track_id = self.get_track()['TrackId']
        # 有可能删除的id不会继续使用
        res = self.post('/Track/@CollectionKeyTestCase_name', json={
            u"TrackId": exists_track_id,
            u'AlbumId': 1,
            u'Bytes': 11170334,
            u'Composer': u'Angus Young, Malcolm Young, Brian Johnson',
            u'Genre': {
                u'GenreId': 1,
                u'Name': u'Rock'
            },
            u'GenreId': 1,
            u'MediaType': {
                u'MediaTypeId': 1,
                u'Name': u'MPEG audio file'
            },
            u'MediaTypeId': 1,
            u'Milliseconds': 343719,
            u'Name': u'CollectionKeyTestCase_name',
            u'UnitPrice': u'0.99',
            u'PlaylistCollection': [
                {
                    u'Name': u"On-The-Go 1",
                    u'PlaylistId': 18
                },
                {
                    u'Name': u"Classical 101 - Deep Cuts",
                    u'PlaylistId': 13
                },
                {
                    u'Name': u"Heavy Metal Classic",
                    u'PlaylistId': 17
                }
            ],
        })
        assert res.status_code == 400
        self.assertRestException(res, "ResourcesAlreadyExists")

    def test_create_exist_resource_with_unique_key(self):
        exists_media_type_name = self.get('/MediaType/1').json()['Name']
        res = self.post('/MediaType/@%s' % exists_media_type_name, json={
            "MediaTypeId": 1,
            "Name": exists_media_type_name,
        })
        assert res.status_code == 400
        self.assertRestException(res, "ResourcesAlreadyExists")

    def test_get_not_exists_resource(self):
        res = self.get('/Track/@NotFound')
        assert res.status_code == 404
        self.assertRestException(res, "ResourceNotFound")

    def test_post_error_type_data(self):
        # TODO 这里没支持过
        res = self.post('/Track/@CollectionKeyTestCase_name', json={
            u'AlbumId': 1,
            u'Bytes': 11170334,
            u'Composer': u'Angus Young, Malcolm Young, Brian Johnson',
            u'Genre': {
                u'GenreId': 1,
                u'Name': u'Rock'
            },
            u'GenreId': 'error_id',
            u'MediaType': {
                u'MediaTypeId': 1,
                u'Name': u'MPEG audio file'
            },
            u'MediaTypeId': 1,
            u'Milliseconds': 343719,
            u'Name': u'CollectionKeyTestCase_name',
            u'UnitPrice': u'0.99',
            u'PlaylistCollection': [
                {
                    u'Name': u"Heavy Metal Classic",
                    u'PlaylistId': 17
                }
            ],
        })
        assert res.status_code == 400

    def test_rewrite_sub_collection(self):
        res = self.put('/Track/@CollectionKeyTestCase_name', json={
            u'AlbumId': 1,
            u'Bytes': 11170334,
            u'Composer': u'Angus Young, Malcolm Young, Brian Johnson',
            u'Genre': {
                u'GenreId': 1,
                u'Name': u'Rock'
            },
            u'GenreId': 1,
            u'MediaType': {
                u'MediaTypeId': 1,
                u'Name': u'MPEG audio file'
            },
            u'MediaTypeId': 1,
            u'Milliseconds': 343719,
            u'Name': u'CollectionKeyTestCase_name',
            u'UnitPrice': u'0.99',
            u'PlaylistCollection': [
                {
                    u'Name': u"Heavy Metal Classic",
                    u'PlaylistId': 17
                }
            ],
        })
        result = self.get('/Track/@CollectionKeyTestCase_name/PlaylistCollection').json()
        assert result['total'] == len(result['items']) == 1
        self.assertListItemEqual(result['items'], [
            {
                u'PlaylistId': 17,
                u'Name': u'Heavy Metal Classic'
            },
        ])

    def test_ensure_primary_key_and_key_field_not_change(self):
        old = self.get('/Track/@CollectionKeyTestCase_name').json()
        res = self.put('/Track/@CollectionKeyTestCase_name', json={
            u'Name': u'CollectionKeyTestCase_name_change',
        })
        assert res.status_code == 400
        self.assertRestException(res, "IllegalRequestData")
        res = self.put('/Track/%s' % old[u'TrackId'], json={
            u'TrackId': old[u'TrackId'] + 1,
        })
        assert res.status_code == 400
        self.assertRestException(res, "IllegalRequestData")

    def test_notnull_field(self):
        # TODO 尚未测试完毕
        res = self.post('/Album/447', json={
            "Title": None,
            "ArtistId": self.exist_artist_id,
        })
        assert res.status_code == 400
        self.assertRestException(res, "IllegalRequestData")
        assert "Title" in res.json()["detail"]

        res = self.post('/Album/447', json={
            "Title": "FakeCreated",
        })
        assert res.status_code == 400
        self.assertRestException(res, "ResourcesConstraintNotNullable")  # 缺少Artist子资源
        assert "ArtistId" in repr(res.json()["detail"])

        res = self.post('/Album/447', json={
            "Title": "TrueCreated",
            "ArtistId": self.exist_artist_id,
        })
        assert res.status_code == 201
        res = self.post('/Album/448', json={
            "Title": "TrueCreated",
            "Artist": {
                "Name": "ExistArtist",
                "ArtistId": self.exist_artist_id,
            }
        })
        assert res.status_code == 201


class CollectionTestCase(SqliteManagerTestBase):
    def setUp(self):
        super(CollectionTestCase, self).setUp()
        self.manager.add(self.Track, methods=['GET', 'POST', "PUT", "DELETE"])
        self.manager.add(self.MediaType, methods=['GET', 'POST', "PUT", "DELETE"])
        self.manager.add(self.Invoice, methods=['GET', 'POST', "PUT", "DELETE"])
        self.manager.add(self.Playlist, methods=['GET', 'POST', "PUT", "DELETE"], key_field="Name")

    def tearDown(self):
        with self.flaskapp.app_context():
            from rest_utils.sa_util import get_session
            from chinook_models import Artist
            all_new_id = [item.ArtistId for item in get_session().query(Artist).filter(Artist.ArtistId > 275).all()]
        for ArtistId in all_new_id:
            res = self.delete('/Artist/%s' % ArtistId)
            assert res.status_code == 204

    def test_get_collection_by_params_success(self):
        result = self.get('/Track', params={
            '_page': 1,
            '_num': 20,
            '_sort': 'TrackId',
            '_direction': 'desc',
            '_expand': 1,
            'Name': "%Inject%",
        }).json()
        assert result == {
            u'items': [{
                u'Album': {
                    u'AlbumId': 1,
                    u'ArtistId': 1,
                    u'Title': u'For Those About To Rock We Salute You'
                },
                u'MediaTypeId': 1,
                u'Name': u'Inject The Venom',
                u'TrackId': 8,
                u'Bytes': 6852860,
                u'MediaType': {
                    u'MediaTypeId': 1,
                    u'Name': u'MPEG audio file'
                },
                u'PlaylistCollection': [
                    {
                        u'PlaylistId': 1,
                        u'Name': u'Music'
                    },
                    {
                        u'PlaylistId': 8,
                        u'Name': u'Music'
                    }
                ],
                u'AlbumId': 1,
                u'Composer': u'Angus Young, Malcolm Young, Brian Johnson',
                u'Genre': {
                    u'GenreId': 1,
                    u'Name': u'Rock'
                },
                u'GenreId': 1,
                u'UnitPrice': u'0.99',
                u'Milliseconds': 210834
            }],
            u'total': 1
        }

    def test_post_form_format_err(self):
        res = self.post('/Track', data='1', headers={
            "Content-Type": 'application/json'
        })
        assert res.status_code == 400
        res = self.post('/Track', data='1', headers={
            "Content-Type": 'application/x-www-form-urlencoded'
        })
        assert res.status_code == 400

    def test_get_collection_by_params_error_name(self):
        res = self.get('/Track', params={
            '_sort': 'ErrorId',
        })
        assert res.status_code == 400
        self.assertRestException(res, "IllegalRequestData")

    def test_get_collection_by_params_error_too_max_expand(self):
        res = self.get('/Track', params={
            '_expand': 11,
        })
        assert res.status_code == 400
        self.assertRestException(res, "RestAssertionError")

    def test_get_not_unique_data(self):
        """
        Playlist表的 key field 存在多个相同数据,在查找的时候会异常
        :return:
        """
        res = self.get('/Playlist/@Music')
        assert res.status_code == 200
        # keyfield存在多个数据不再报错
        # self.assertRestException(res, "UniqueCheckError")

    def test_get_collection_by_params_list_success(self):
        result = self.get('/MediaType', params={
            '_sort': 'MediaTypeId',
            '_direction': 'asc',
            '_expand': 1,
            'MediaTypeId[]': [
                1, 2, 3
            ],
        }).json()
        assert result == {
            u'items': [
                {
                    u"MediaTypeId": 1,
                    u"Name": u"MPEG audio file",
                },
                {
                    u"MediaTypeId": 2,
                    u"Name": u"Protected AAC audio file",
                },
                {
                    u"MediaTypeId": 3,
                    u"Name": u"Protected MPEG-4 video file",
                },

            ],
            u'total': 3
        }

    def test_get_collection_by_params_orders_desc_success(self):
        result = self.get('/Invoice', params={
            '_orders': 'BillingCity:asc,Total:desc',
            "_num": 3,
        }).json()
        assert result == {
            u'items': [
                {
                    u'InvoiceId': 390,
                    u'InvoiceDate': u'2013-09-12 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'13.86',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                },
                {
                    u'InvoiceId': 206,
                    u'InvoiceDate': u'2011-06-21 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'8.94',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                },
                {
                    u'InvoiceId': 32,
                    u'InvoiceDate': u'2009-05-10 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'8.91',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                }
            ],
            u'total': 412
        }

    def test_get_collection_by_params_orders_desc_success_list(self):
        result = self.get('/Invoice', params={
            '_orders[]': [
                "BillingCity:asc",
                "Total:desc"
            ],
            "_num": 3,
        }).json()
        assert result == {
            u'items': [
                {
                    u'InvoiceId': 390,
                    u'InvoiceDate': u'2013-09-12 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'13.86',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                },
                {
                    u'InvoiceId': 206,
                    u'InvoiceDate': u'2011-06-21 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'8.94',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                },
                {
                    u'InvoiceId': 32,
                    u'InvoiceDate': u'2009-05-10 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'8.91',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                }
            ],
            u'total': 412
        }

    def test_get_collection_by_params_orders_asc_success(self):
        result = self.get('/Invoice', params={
            '_orders': 'BillingCity:asc,Total:asc',
            "_num": 3,
        }).json()
        assert result == {
            u'items': [
                {
                    u'InvoiceId': 258,
                    u'InvoiceDate': u'2012-02-09 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'0.99',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                },
                {
                    u'InvoiceId': 161,
                    u'InvoiceDate': u'2010-12-15 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'1.98',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                },
                {
                    u'InvoiceId': 379,
                    u'InvoiceDate': u'2013-08-02 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'1.98',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                }
            ],
            u'total': 412
        }

    def test_get_collection_by_params_orders_no_success(self):
        result = self.get('/Invoice', params={
            '_orders': 'BillingCity:asc,Total',
            "_num": 3,
        }).json()
        assert result == {
            u'items': [
                {
                    u'InvoiceId': 258,
                    u'InvoiceDate': u'2012-02-09 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'0.99',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                },
                {
                    u'InvoiceId': 161,
                    u'InvoiceDate': u'2010-12-15 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'1.98',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                },
                {
                    u'InvoiceId': 379,
                    u'InvoiceDate': u'2013-08-02 00:00:00',
                    u'BillingPostalCode': u'1016',
                    u'BillingState': u'VV',
                    u'BillingAddress': u'Lijnbaansgracht 120bg',
                    u'BillingCountry': u'Netherlands',
                    u'Total': u'1.98',
                    u'CustomerId': 48,
                    u'BillingCity': u'Amsterdam'
                }
            ],
            u'total': 412
        }

    def test_get_collection_by_params_chinese(self):
        result = self.get('/Track', params={
            '_expand': 1,
            'Name': u"%测试%",
        }).json()
        assert result == {
            u'items': [],
            u'total': 0
        }

    def test_get_collection_by_params_sub_resource(self):
        Classical = self.get('/Track', params={
            'PlaylistCollection.Name': u"Classical",
            '_expand': 1,
        }).json()
        Classical_num = Classical[u'total']
        assert Classical_num == 75
        Classical_Grunge = self.get('/Track', params={
            'PlaylistCollection.Name[]': [
                u"Classical",
                u"Grunge",
            ],
            '_expand': 1,
        }).json()
        Classical_Grunge_num = Classical_Grunge[u'total']
        assert Classical_Grunge_num == 90
        Grunge = self.get('/Track', params={
            'PlaylistCollection.Name[]': [
                u"Grunge",
            ],
            '_expand': 1,
        }).json()
        assert Grunge[u'total'] == Classical_Grunge_num - Classical_num

    def test_get_collection_by_params_fields(self):
        result = self.get('/Track', params={
            '_page': 1,
            '_num': 20,
            '_sort': 'TrackId',
            '_direction': 'desc',
            '_expand': 1,
            'Name': "%Inject%",
            '_fields': "Track:TrackId,PlaylistCollection;Playlist:PlaylistId"
        }).json()
        assert result == {
            u'items': [{
                u'TrackId': 8,
                u'PlaylistCollection': [
                    {
                        u'PlaylistId': 1
                    },
                    {
                        u'PlaylistId': 8
                    }
                ],
            }],
            u'total': 1
        }

    def test_get_collection_by_params_fields_list(self):
        result = self.get('/Track', params={
            '_page': 1,
            '_num': 20,
            '_sort': 'TrackId',
            '_direction': 'desc',
            '_expand': 1,
            'Name': "%Inject%",
            '_fields[]': [
                "Track:TrackId,PlaylistCollection",
                "Playlist:PlaylistId",
            ]
        }).json()
        assert result == {
            u'items': [{
                u'TrackId': 8,
                u'PlaylistCollection': [
                    {
                        u'PlaylistId': 1
                    },
                    {
                        u'PlaylistId': 8
                    }
                ],
            }],
            u'total': 1
        }

    def test_get_collection_by_params_match_main(self):
        self.manager.add(
            self.Customer,
            methods=['GET', 'POST', "PUT", "DELETE"],
            match_fields=['Address', 'LastName']
        )
        # LastName
        result = self.get('/Customer', params={
            '_page': 1,
            '_num': 20,
            '_sort': 'CustomerId',
            '_match': 'Peeters',
            '_fields[]': [
                "Customer:CustomerId"
            ]
        }).json()
        assert result == {
            u'items': [{
                u'CustomerId': 8,
            }],
            u'total': 1
        }
        # LastName Address
        result = self.get('/Customer', params={
            '_sort': 'CustomerId',
            '_match': 'Br',
            '_fields[]': [
                'Customer:CustomerId'
            ]
        }).json()
        assert result == {
            'items': [
                {
                    u'CustomerId': 1,
                },
                {
                    u'CustomerId': 18,
                },
                {
                    u'CustomerId': 29,
                },
            ],
            u'total': 3,
        }
        # LastName
        result = self.get('/Customer', params={
            '_sort': 'CustomerId',
            '_match': 'Br%',
            '_fields[]': [
                'Customer:CustomerId'
            ]
        }).json()
        assert result == {
            'items': [
                {
                    u'CustomerId': 18,
                },
                {
                    u'CustomerId': 29,
                },
            ],
            u'total': 2,
        }

    def test_get_collection_by_params_except_list(self):
        result = self.get('/Track', params={
            '_page': 1,
            '_num': 20,
            '_sort': 'TrackId',
            '_direction': 'desc',
            '_expand': 1,
            'Name': "%Inject%",
            '_except[]': [
                "Track:Name,AlbumId,MediaTypeId,GenreId,Composer,Milliseconds,Bytes,UnitPrice,Album,Genre,MediaType",
                "Playlist:Name",
            ]
        }).json()
        assert result == {
            u'items': [{
                u'TrackId': 8,
                u'PlaylistCollection': [
                    {
                        u'PlaylistId': 1
                    },
                    {
                        u'PlaylistId': 8
                    }
                ],
            }],
            u'total': 1
        }

    def test_get_collection_by_params_match_sub_resource(self):
        self.manager.add(
            self.Customer,
            methods=['GET', 'POST', "PUT", "DELETE"],
            match_fields=['Address', 'LastName']
        )
        # BillingCountry
        result = self.get('/Customer', params={
            '_page': 1,
            '_num': 1,
            '_sort': 'CustomerId',
            '_match': 'Br',
            '_expand': 1,
            '_fields[]': [
                "Customer:CustomerId,Invoices",
                "Invoice:InvoiceId"
            ]
        }).json()
        assert result['items'][0]['CustomerId'] == 1
        self.assert_almost_like_list(
            result['items'][0]['Invoices'],
            [
                {
                    u'InvoiceId': 98,
                },
                {
                    u'InvoiceId': 121,
                },
                {
                    u'InvoiceId': 143,
                },
                {
                    u'InvoiceId': 195,
                },
                {
                    u'InvoiceId': 316,
                },
                {
                    u'InvoiceId': 327,
                },
                {
                    u'InvoiceId': 382,
                }
            ]
        )
        # 'BillingAddress', 'BillingCountry'
        result = self.get('/Customer', params={
            '_page': 1,
            '_num': 20,
            '_sort': 'CustomerId',
            'Invoices._match': 'Campos',
            '_expand': 1,
            '_fields[]': [
                "Customer:CustomerId,Invoices",
                "Invoice:InvoiceId"
            ]
        }).json()
        assert result['items'][0]['CustomerId'] == 1
        self.assert_almost_like_list(
            result['items'][0]['Invoices'],
            [
                {
                    u'InvoiceId': 98,
                },
                {
                    u'InvoiceId': 121,
                },
                {
                    u'InvoiceId': 143,
                },
                {
                    u'InvoiceId': 195,
                },
                {
                    u'InvoiceId': 316,
                },
                {
                    u'InvoiceId': 327,
                },
                {
                    u'InvoiceId': 382,
                }
            ]
        )

    def test_get_collection_by_params_sub_one(self):
        self.manager.add(
            self.Customer,
            methods=['GET', 'POST', "PUT", "DELETE"],
            match_fields=['Address', 'LastName']
        )
        # support uselist=false
        result = self.get('/Customer', params={
            '_page': 1,
            '_num': 20,
            '_sort': 'CustomerId',
            'Employee.LastName': 'Johnson',
            'CustomerId': [
                2, 3, 4, 5
            ],
            '_fields[]': [
                "Customer:CustomerId"
            ]
        }).json()
        assert result == {
            u'items': [{
                u'CustomerId': 2,
            }],
            u'total': 1
        }
