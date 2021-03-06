from nose.tools import eq_
from pyquery import PyQuery as pq

import amo
import amo.tests
from amo.utils import urlparams
from amo.urlresolvers import reverse

from addons.models import Category, AddonCategory
from mkt.webapps.models import Webapp
from mkt.zadmin.models import FeaturedApp


class TestFeaturedApps(amo.tests.TestCase):
    fixtures = ['base/users']
    def setUp(self):
        self.c1 = Category.objects.create(name='awesome',
                                     type=amo.ADDON_WEBAPP)
        self.c2 = Category.objects.create(name='groovy',
                                     type=amo.ADDON_WEBAPP)

        self.a1 = Webapp.objects.create(status=amo.STATUS_PUBLIC,
                                        name='awesome app 1',
                                        type=amo.ADDON_WEBAPP)
        self.a2 = Webapp.objects.create(status=amo.STATUS_PUBLIC,
                                        name='awesome app 2',
                                        type=amo.ADDON_WEBAPP)
        self.g1 = Webapp.objects.create(status=amo.STATUS_PUBLIC,
                                        name='groovy app 1',
                                        type=amo.ADDON_WEBAPP)
        self.s1 = Webapp.objects.create(status=amo.STATUS_PUBLIC,
                                        name='splendid app 1',
                                        type=amo.ADDON_WEBAPP)
        AddonCategory.objects.create(category=self.c1, addon=self.a1)
        AddonCategory.objects.create(category=self.c1, addon=self.a2)

        AddonCategory.objects.create(category=self.c2, addon=self.g1)

        AddonCategory.objects.create(category=self.c1, addon=self.s1)
        AddonCategory.objects.create(category=self.c2, addon=self.s1)

        self.client.login(username='admin@mozilla.com', password='password')
        self.url = reverse('zadmin.featured_apps_ajax')

    def test_get_featured_apps(self):
        r = self.client.get(urlparams(self.url, category=self.c1.id))
        assert not r.content

        f1 = FeaturedApp.objects.create(app=self.a1, category=self.c1)
        f2 = FeaturedApp.objects.create(app=self.s1, category=self.c2, is_sponsor=True)
        r = self.client.get(urlparams(self.url, category=self.c1.id))
        doc = pq(r.content)
        eq_(len(doc), 1)
        eq_(doc('table td').eq(1).text(), 'awesome app 1')
        eq_(doc('table td').eq(4).text(), 'Not sponsored')

        r = self.client.get(urlparams(self.url, category=self.c2.id))
        doc = pq(r.content)
        eq_(len(doc), 1)
        eq_(doc('table td').eq(1).text(), 'splendid app 1')
        eq_(doc('table td').eq(4).text(), 'Sponsored')


    def test_get_categories(self):
        url = reverse('zadmin.featured_categories_ajax')
        FeaturedApp.objects.create(app=self.a1, category=self.c1)
        FeaturedApp.objects.create(app=self.a2, category=self.c1)
        FeaturedApp.objects.create(app=self.a2, category=None)
        r = self.client.get(url)
        doc = pq(r.content)
        eq_(set(pq(x).text() for x in doc[0]),
            set(['Home Page (1)', 'groovy (0)', 'awesome (2)']))

    def test_add_featured_app(self):
        self.client.post(self.url,
                         {'category': '',
                          'add': self.a1.id})
        assert FeaturedApp.objects.filter(app=self.a1.id,
                                          category=None).exists()

        self.client.post(self.url,
                         {'category': self.c1.id,
                          'add': self.a1.id})
        assert FeaturedApp.objects.filter(app=self.a1,
                                          category=self.c1).exists()

    def test_delete_featured_app(self):
        FeaturedApp.objects.create(app=self.a1, category=None)
        FeaturedApp.objects.create(app=self.a1, category=self.c1)
        self.client.post(self.url,
                         {'category': '',
                          'delete': self.a1.id})
        assert not FeaturedApp.objects.filter(app=self.a1,
                                              category=None).exists()
        assert FeaturedApp.objects.filter(app=self.a1,
                                          category=self.c1).exists()
        FeaturedApp.objects.create(app=self.a1, category=None)
        self.client.post(self.url,
                         {'category': self.c1.id,
                          'delete': self.a1.id})
        assert not FeaturedApp.objects.filter(app=self.a1,
                                              category=self.c1).exists()
