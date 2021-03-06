import operator
from datetime import date, timedelta, datetime

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Region, Product, Client, SalesMan, Transaction, PercentileInfo
from .utils import proper_paginate, ResolveModel

pageint = 10
serial = []
pairs = []


def cmp(client):
    return dic[client]


def test(request):
    pass


@login_required
def index(request):
    return render(request, 'main/index.html', {
        'products': Product.objects.all(),
        'clients': Client.objects.all(),
        'regions': Region.objects.all(),
        'salesMans': SalesMan.objects.all()
    })


@login_required
def productIndex(request):
    return render(request, 'main/index-product.html', {
        'products': Product.objects.all().order_by('name'),
        'clients': Client.objects.all(),
        'regions': Region.objects.all(),
        'salesMans': SalesMan.objects.all()
    })


@login_required
def clientIndex(request):
    return render(request, 'main/index-client.html', {
        'products': Product.objects.all(),
        'clients': Client.objects.all(),
        'regions': Region.objects.all(),
        'salesMans': SalesMan.objects.all()
    })


@login_required
def regionIndex(request):
    return render(request, 'main/index-region.html', {
        'products': Product.objects.all(),
        'clients': Client.objects.all(),
        'regions': Region.objects.all(),
        'salesMans': SalesMan.objects.all()
    })


@login_required
def salesmanIndex(request):
    return render(request, 'main/index-salesman.html', {
        'products': Product.objects.all(),
        'clients': Client.objects.all(),
        'regions': Region.objects.all(),
        'salesMans': SalesMan.objects.all().order_by('name')
    })


# @api_view
# def DefaultIndex(request):
# 	model 	= ResolveModel(request.GET['modelName'])

@login_required
def product(request, *args, **kwargs):
    product = get_object_or_404(Product.objects.all(), pk=kwargs['id'])
    return render(request, 'main/product.html', {'product': product,
                                                 'products': Product.objects.all(),
                                                 'clients': Client.objects.all(),
                                                 'regions': Region.objects.all(),
                                                 'salesMans': SalesMan.objects.all()})


@login_required
def client(request, *args, **kwargs):
    client = get_object_or_404(Client, pk=kwargs['id'])
    return render(request, 'main/client.html', {'client': client,
                                                'products': Product.objects.all(),
                                                'clients': Client.objects.all(),
                                                'regions': Region.objects.all(),
                                                'salesMans': SalesMan.objects.all()})


@login_required
def region(request, *args, **kwargs):
    region = get_object_or_404(Region, pk=kwargs['id'])
    return render(request, 'main/region.html', {'region': region,
                                                'products': Product.objects.all(),
                                                'clients': Client.objects.all(),
                                                'regions': Region.objects.all(),
                                                'salesMans': SalesMan.objects.all()})


@login_required
def salesman(request, *args, **kwargs):
    salesman = get_object_or_404(SalesMan, pk=kwargs['id'])
    return render(request, 'main/salesman.html', {'salesman': salesman,
                                                  'products': Product.objects.all(),
                                                  'clients': Client.objects.all(),
                                                  'regions': Region.objects.all(),
                                                  'salesMans': SalesMan.objects.all()})


class ChartView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        model = ResolveModel(request.GET['modelName'])
        transactions = []
        if model == Product:
            transactions = Transaction.objects.filter(product__id=request.GET['product'])
        if model == Client:
            transactions = Transaction.objects.filter(client__id=request.GET['client'])

        if model == Region:
            transactions = Transaction.objects.filter(client__region__id=request.GET['region'])

        if model == SalesMan:
            transactions = Transaction.objects.filter(client__salesman__id=request.GET['salesman'])
        transactions = transactions.filter(t_type='PURCHASE')

        beginDate = Transaction.objects.last().date
        endDate = Transaction.objects.first().date

        if request.GET['beginDate'] != '':
            beginDate = datetime.strptime(request.GET.get('beginDate', '1900-01-01'), '%Y-%m-%d').date()
        if request.GET['endDate'] != '':
            endDate = datetime.strptime(request.GET.get('endDate', '1900-01-01'), '%Y-%m-%d').date()

        transactions = transactions.filter(
            date__gte=beginDate, date__lte=endDate
        )

        if request.GET['product'] != '':
            transactions = transactions.filter(product_id=request.GET['product'])

        if request.GET['client'] != '':
            transactions = transactions.filter(client__id=request.GET['client'])
        if request.GET['region'] != '':
            transactions = transactions.filter(client__region__id=request.GET['region'])
        if request.GET['salesman'] != '':
            transactions = transactions.filter(client__salesman__id=request.GET['salesman'])

        beginDate = beginDate.replace(day=1)
        endDate = (endDate.replace(day=1) + timedelta(days=32)).replace(day=1)
        label = []
        dic_volume = {}
        dic_amount = {}
        while beginDate < endDate:
            out = beginDate.strftime('%b %y')
            label.append(out)
            dic_volume[out] = 0
            dic_amount[out] = 0
            beginDate = (beginDate + timedelta(days=32)).replace(day=1)

        for t in transactions:
            out = t.date.strftime('%b %y')
            dic_volume[out] += t.volume
            dic_amount[out] += t.amount

        data = {
            'label': label,
            'volume': [dic_volume[x] for x in label],
            'tk': [dic_amount[x] for x in label],
        }
        return Response(data)


class DiscountImpactView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def getAmountChangePercentage(self, beforeAmount, afterAmount):
        if beforeAmount == 0:
            return 'N/A'
        else:
            return str(round(((afterAmount - beforeAmount) / beforeAmount) * 100, 2)) + '%'

    def get(self, request, *args, **kwargs):
        model = ResolveModel(request.GET['modelName'])
        transactions = []
        if model == Product:
            transactions = Transaction.objects.filter(product__id=request.GET['product'])
        if model == Client:
            transactions = Transaction.objects.filter(client__id=request.GET['client'])
        if model == Region:
            transactions = Transaction.objects.filter(client__region__id=request.GET['region'])
        if model == SalesMan:
            transactions = Transaction.objects.filter(client__salesman__id=request.GET['salesman'])

        if request.GET['product'] != '':
            transactions = transactions.filter(product_id=request.GET['product'])
        if request.GET['client'] != '':
            transactions = transactions.filter(client__id=request.GET['client'])
        if request.GET['region'] != '':
            transactions = transactions.filter(client__region__id=request.GET['region'])
        if request.GET['salesman'] != '':
            transactions = transactions.filter(client__salesman__id=request.GET['salesman'])
        transactions = transactions.order_by('date')

        monthPrevIdx = 0
        monthAfterIdx = transactions.count() - 1
        monthPrevAmount = 0
        monthAfterAmount = 0
        discountCount = 0
        dataRaw = []
        duration = 3
        if request.GET['duration'] == '6':
            duration = 6
        for i in range(transactions.count()):
            if transactions[i].t_type == 'PURCHASE':
                monthPrevAmount = monthPrevAmount + transactions[i].amount
            elif transactions[i].t_type == 'DISCOUNT':
                while True:
                    delta = transactions[i].date - transactions[monthPrevIdx].date
                    if delta.days <= duration * 30:
                        break
                    else:
                        if transactions[monthPrevIdx].t_type == 'PURCHASE':
                            monthPrevAmount = monthPrevAmount - transactions[monthPrevIdx].amount
                        monthPrevIdx = monthPrevIdx + 1
                discountCount = discountCount + 1
                dataRaw.append({
                    'date': transactions[i].date.strftime('%b %d, %Y'),
                    'discountAmount': transactions[i].amount,
                    'monthsPrevAmount': monthPrevAmount,
                    'monthsAfterAmount': 0
                })
        for i in reversed(range(transactions.count())):
            if transactions[i].t_type == 'PURCHASE':
                monthAfterAmount = monthAfterAmount + transactions[i].amount
            elif transactions[i].t_type == 'DISCOUNT':
                while True:
                    delta = transactions[monthAfterIdx].date - transactions[i].date
                    if delta.days <= duration * 30:
                        break
                    else:
                        if transactions[monthAfterIdx].t_type == 'PURCHASE':
                            monthAfterAmount = monthAfterAmount - transactions[monthAfterIdx].amount
                        monthAfterIdx = monthAfterIdx - 1
                discountCount = discountCount - 1
                dataRaw[discountCount]['monthsAfterAmount'] = monthAfterAmount
        data = {
            'labels': [['Date: ' + d['date'],
                        'Discount: ' + str(d['discountAmount']) + ' Tk',
                        'Amount change : ' + self.getAmountChangePercentage(d['monthsPrevAmount'],
                                                                            d['monthsAfterAmount'])
                        ] for d in dataRaw],
            'beforeAmounts': [d['monthsPrevAmount'] for d in dataRaw],
            'afterAmounts': [d['monthsAfterAmount'] for d in dataRaw]
        }
        return Response(data)


class DefaultView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        model = ResolveModel(request.GET['modelName'])

        if request.GET['queryType'] == 'volume':
            q = model.objects.order_by('-volume')
        else:
            q = model.objects.order_by('-amount')
        output = [(x, x.volume, x.amount) for x in q]

        t_html = 'main/includes/' + request.GET['modelName'] + '-table.html'

        # return Response(getData(request, output, 10, request.GET.get('page', 1), 'main/includes/product-table.html'))
        paginator = Paginator(output, pageint)
        page = request.GET.get('page', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            rows = paginator.page(page)
        except PageNotAnInteger:
            rows = paginator.page(1)
        except EmptyPage:
            rows = paginator.page(paginator.num_pages)

        data = {
            'table': render_to_string(t_html,
                                      {'objects': rows, 'page-page_range': pg, 'queryType': request.GET['queryType']}),
            'paginator': render_to_string('main/includes/Paginator.html', {'page': rows, 'page_range': pg,
                                                                           'id': request.GET['modelName'] + "-" +
                                                                                 request.GET['queryType']})
        }
        return Response(data)


class DistributionView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if 'product' in request.GET and request.GET['product'] != '':
            transactions = Transaction.objects.all()
            transactions = transactions.filter(t_type='PURCHASE')
            transactions = transactions.filter(product__id=request.GET['product'])
            totalAmount = 0
            tk = {}
            for t in transactions:
                totalAmount += t.amount
                key = '-'
                if request.GET['modelName'] == 'Region':
                    key = t.client.region
                if key in tk:
                    tk[key] += t.amount
                else:
                    tk[key] = t.amount

            sorted_tk = sorted(tk.items(), key=operator.itemgetter(1))
            data = {
                'labels': [],
                'amounts': []
            }
            for key, value in tk.items():
                data['labels'].append(key.name + ' (' + str(round((value * 100) / totalAmount, 2)) + '%)')
                data['amounts'].append(value)
            return Response(data)
        else:
            model = ResolveModel(request.GET['modelName'])
            q = model.objects.all().order_by('-amount')
            totalAmount = 0
            for d in q:
                totalAmount = totalAmount + d.amount
            data = {
                'labels': [d.name + ' (' + str(round((d.amount * 100) / totalAmount, 2)) + '%)' for d in q],
                'amounts': [d.amount for d in q]
            }
            return Response(data)


class CompareView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        # TO DO
        print(request.GET)
        low = date.today()
        high = low.replace(year=1990)
        low = Transaction.objects.last().date
        high = Transaction.objects.first().date
        if request.GET['beginDate'] != '':
            low = datetime.strptime(request.GET.get('beginDate', '1900-01-01'), '%Y-%m-%d').date()
        if request.GET['endDate'] != '':
            high = datetime.strptime(request.GET.get('endDate', '1900-01-01'), '%Y-%m-%d').date()

        print(low, high)
        if (low > high): low, high = high, low
        # transactions = Transaction.objects.all()
        transactions = Transaction.objects.filter(
            date__gte=low, date__lte=high
        )

        if request.GET['product'] != '':
            transactions = transactions.filter(product_id=request.GET['product'])
        if request.GET['client'] != '':
            transactions = transactions.filter(client__id=request.GET['client'])
        if request.GET['region'] != '':
            transactions = transactions.filter(client__region__id=request.GET['region'])
        if request.GET['salesman'] != '':
            transactions = transactions.filter(client__salesman__id=request.GET['salesman'])
        transactions = transactions.filter(t_type='PURCHASE')

        print(len(transactions))
        if (request.GET['modelName'] == 'SalesMan'):
            ob1 = transactions.filter(client__salesman__id=request.GET['p1'])
            ob2 = transactions.filter(client__salesman__id=request.GET['p2'])
        elif (request.GET['modelName'] == 'Product'):
            ob1 = transactions.filter(product__id=request.GET['p1'])
            ob2 = transactions.filter(product__id=request.GET['p2'])

        print(len(ob1))
        print(len(ob2))
        print(high, low)
        option = request.GET['queryType']
        dic = {}
        dic2 = {}
        for t in ob1:
            out = t.date.strftime('%b %y')
            if option == 'volume':
                add = t.volume
            else:
                add = t.amount

            if out in dic:
                dic[out] += add
            else:
                dic[out] = add

            low = min(low, t.date)
            high = max(high, t.date)

        for t in ob2:
            out = t.date.strftime('%b %y')
            if option == 'volume':
                add = t.volume
            else:
                add = t.amount

            if out in dic2:
                dic2[out] += add
            else:
                dic2[out] = add

            low = min(low, t.date)
            high = max(high, t.date)

        low = low.replace(day=1)
        high = (high + timedelta(days=32)).replace(day=1)
        label = []
        ret1 = []
        ret2 = []

        while low < high:
            out = low.strftime('%b %y')
            label.append(out)
            if out in dic:
                ret1.append(dic[out])
            else:
                ret1.append(0)

            if out in dic2:
                ret2.append(dic2[out])
            else:
                ret2.append(0)

            low = (low + timedelta(days=32)).replace(day=1)

        data = {
            'volume': ret1,
            'tk': ret2,
            'label': label,
        }
        return Response(data)


class ProductView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        print(request.GET)

        beginDate = datetime.strptime('1900-01-01', '%Y-%m-%d').date()
        endDate = date.today()

        if request.GET['beginDate'] != '':
            beginDate = datetime.strptime(request.GET.get('beginDate', '1900-01-01'), '%Y-%m-%d').date()
        if request.GET['endDate'] != '':
            endDate = datetime.strptime(request.GET.get('endDate', '1900-01-01'), '%Y-%m-%d').date()

        transactions = Transaction.objects.filter(
            date__gte=beginDate, date__lte=endDate
        )

        if request.GET['client'] != '':
            transactions = transactions.filter(client__id=request.GET['client'])
        if request.GET['region'] != '':
            transactions = transactions.filter(client__region__id=request.GET['region'])
        if request.GET['salesman'] != '':
            transactions = transactions.filter(client__salesman__id=request.GET['salesman'])

        products = Product.objects.all()
        MapforVolume = {}
        MapForTk = {}
        for p in products:
            MapforVolume[p.id] = 0
            MapForTk[p.id] = 0

        for i in transactions:
            if i.t_type != 'PURCHASE':
                continue
            MapForTk[i.product.id] += i.amount
            MapforVolume[i.product.id] += i.volume

        output = [(p, MapforVolume[p.id], MapForTk[p.id]) for p in products]
        if request.GET['queryType'] == 'volume':
            output = sorted(output, key=lambda x: x[1], reverse=True)
        elif request.GET['queryType'] == 'tk':
            output = sorted(output, key=lambda x: x[2], reverse=True)

        # return Response(getData(request, output, 10, request.GET.get('page', 1), 'main/includes/product-table.html'))
        paginator = Paginator(output, pageint)
        page = request.GET.get('page', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            rows = paginator.page(page)
        except PageNotAnInteger:
            rows = paginator.page(1)
        except EmptyPage:
            rows = paginator.page(paginator.num_pages)

        data = {
            'table': render_to_string('main/includes/Product-table.html',
                                      {'objects': rows, 'page-page_range': pg, 'queryType': request.GET['queryType']}),
            'paginator': render_to_string('main/includes/Paginator.html',
                                          {'page': rows, 'page_range': pg, 'id': "Product-" + request.GET['queryType']})
        }
        return Response(data)


class ClientView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):

        beginDate = datetime.strptime('1900-01-01', '%Y-%m-%d').date()
        endDate = date.today()

        if request.GET['beginDate'] != '':
            beginDate = datetime.strptime(request.GET.get('beginDate', '1900-01-01'), '%Y-%m-%d').date()
        if request.GET['endDate'] != '':
            endDate = datetime.strptime(request.GET.get('endDate', '1900-01-01'), '%Y-%m-%d').date()

        transactions = Transaction.objects.filter(
            date__gte=beginDate, date__lte=endDate
        )

        if request.GET['product'] != '':
            transactions = transactions.filter(product__id=request.GET['product'])
        if request.GET['region'] != '':
            transactions = transactions.filter(client__region__id=request.GET['region'])
        if request.GET['salesman'] != '':
            transactions = transactions.filter(client__salesman__id=request.GET['salesman'])
        transactions = transactions.filter(t_type='PURCHASE')

        clients = Client.objects.all()
        MapforVolume = {}
        MapForTk = {}
        for c in clients:
            MapforVolume[c.id] = 0
            MapForTk[c.id] = 0

        for i in transactions:
            MapForTk[i.client.id] += i.amount
            MapforVolume[i.client.id] += i.volume

        output = [(c, MapforVolume[c.id], MapForTk[c.id]) for c in clients]
        if request.GET['queryType'] == 'volume':
            output = sorted(output, key=lambda x: x[1], reverse=True)
        elif request.GET['queryType'] == 'tk':
            output = sorted(output, key=lambda x: x[2], reverse=True)

        paginator = Paginator(output, pageint)
        page = request.GET.get('page', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            rows = paginator.page(page)
        except PageNotAnInteger:
            rows = paginator.page(1)
        except EmptyPage:
            rows = paginator.page(paginator.num_pages)

        data = {
            'table': render_to_string('main/includes/Client-table.html', {'objects': rows, 'page-page_range': pg}),
            'paginator': render_to_string('main/includes/Paginator.html',
                                          {'page': rows, 'page_range': pg, 'id': "Client-" + request.GET['queryType']})

        }
        return Response(data)


class RegionView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):

        beginDate = datetime.strptime('1900-01-01', '%Y-%m-%d').date()
        endDate = date.today()

        if request.GET['beginDate'] != '':
            beginDate = datetime.strptime(request.GET.get('beginDate', '1900-01-01'), '%Y-%m-%d').date()
        if request.GET['endDate'] != '':
            endDate = datetime.strptime(request.GET.get('endDate', '1900-01-01'), '%Y-%m-%d').date()

        transactions = Transaction.objects.filter(
            date__gte=beginDate, date__lte=endDate
        )

        if request.GET['product'] != '':
            transactions = transactions.filter(product__id=request.GET['product'])
        if request.GET['client'] != '':
            transactions = transactions.filter(client__id=request.GET['client'])
        if request.GET['salesman'] != '':
            transactions = transactions.filter(lient__salesman__id=request.GET['salesman'])
        transactions = transactions.filter(t_type='PURCHASE')

        regions = Region.objects.all()
        MapforVolume = {}
        MapForTk = {}
        for r in regions:
            MapforVolume[r.id] = 0
            MapForTk[r.id] = 0

        for i in transactions:
            MapForTk[i.client.region.id] += i.amount
            MapforVolume[i.client.region.id] += i.volume

        output = [(r, MapforVolume[r.id], MapForTk[r.id]) for r in regions]
        if request.GET['queryType'] == 'volume':
            output = sorted(output, key=lambda x: x[1], reverse=True)
        elif request.GET['queryType'] == 'tk':
            output = sorted(output, key=lambda x: x[2], reverse=True)

        paginator = Paginator(output, pageint)
        page = request.GET.get('page', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            rows = paginator.page(page)
        except PageNotAnInteger:
            rows = paginator.page(1)
        except EmptyPage:
            rows = paginator.page(paginator.num_pages)

        data = {
            'table': render_to_string('main/includes/Region-table.html', {'objects': rows, 'page-page_range': pg}),
            'paginator': render_to_string('main/includes/Paginator.html',
                                          {'page': rows, 'page_range': pg, 'id': "Region-" + request.GET['queryType']})

        }
        return Response(data)


class SalesManView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):

        beginDate = datetime.strptime('1900-01-01', '%Y-%m-%d').date()
        endDate = date.today()

        if request.GET['beginDate'] != '':
            beginDate = datetime.strptime(request.GET.get('beginDate', '1900-01-01'), '%Y-%m-%d').date()
        if request.GET['endDate'] != '':
            endDate = datetime.strptime(request.GET.get('endDate', '1900-01-01'), '%Y-%m-%d').date()

        transactions = Transaction.objects.filter(
            date__gte=beginDate, date__lte=endDate
        )

        if request.GET['product'] != '':
            transactions = transactions.filter(product__id=request.GET['product'])
        if request.GET['client'] != '':
            transactions = transactions.filter(client__id=request.GET['client'])
        if request.GET['region'] != '':
            transactions = transactions.filter(client__region__id=request.GET['region'])
        transactions = transactions.filter(t_type='PURCHASE')

        salesMans = SalesMan.objects.all()
        MapforVolume = {}
        MapForTk = {}
        for r in salesMans:
            MapforVolume[r.id] = 0
            MapForTk[r.id] = 0

        for i in transactions:
            MapForTk[i.client.salesman.id] += i.amount
            MapforVolume[i.client.salesman.id] += i.volume

        output = [(r, MapforVolume[r.id], MapForTk[r.id]) for r in salesMans]
        if request.GET['queryType'] == 'volume':
            output = sorted(output, key=lambda x: x[1], reverse=True)
        elif request.GET['queryType'] == 'tk':
            output = sorted(output, key=lambda x: x[2], reverse=True)

        paginator = Paginator(output, pageint)
        page = request.GET.get('page', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            rows = paginator.page(page)
        except PageNotAnInteger:
            rows = paginator.page(1)
        except EmptyPage:
            rows = paginator.page(paginator.num_pages)

        data = {
            'table': render_to_string('main/includes/SalesMan-table.html', {'objects': rows, 'page-page_range': pg}),
            'paginator': render_to_string('main/includes/Paginator.html', {'page': rows, 'page_range': pg,
                                                                           'id': "SalesMan-" + request.GET[
                                                                               'queryType']})
        }
        return Response(data)


class LoadProduct(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def addMonthsToDate(self, dateVal, monthVal):
        yearDiff = monthVal // 12
        monthVal -= yearDiff * 12
        dayOneDateVal = dateVal.replace(year=dateVal.year + yearDiff, day=1)
        if dateVal.month + monthVal > 12:
            return dayOneDateVal.replace(year=dayOneDateVal.year + 1, month=monthVal - (12 - dayOneDateVal.month))
        else:
            return dayOneDateVal.replace(month=dayOneDateVal.month + monthVal)

    def getMWAPrediction3(self, val1, val2, val3):
        return int(val1 * 0.65 + val2 * 0.25 + val3 * 0.1)

    def getMWAPrediction2(self, val1, val2):
        return int(val1 * 0.75 + val2 * 0.25)

    def getLSRPrediction3(self, val1, val2, val3):
        return int(val1 + (val1 - val2) * 0.7 + (val2 - val3) * 0.3)

    def getLSRPrediction2(self, val1, val2):
        return int(val1 + (val1 - val2))

    def getPrediction3(self, val1, val2, val3):
        return max(0,
                   int(self.getMWAPrediction3(val1, val2, val3) * 0.5 + self.getLSRPrediction3(val1, val2, val3) * 0.5))

    def getPrediction2(self, val1, val2):
        return max(0, int(self.getMWAPrediction2(val1, val2)))

    def get(self, request, *args, **kwargs):
        transactions = Transaction.objects.all()
        transactions = transactions.filter(t_type='PURCHASE')

        if 'product' in request.GET and request.GET['product'] != '':
            transactions = transactions.filter(product__id=request.GET['product'])

        if 'client' in request.GET and request.GET['client'] != '':
            transactions = transactions.filter(client__id=request.GET['client'])

        if 'salesman' in request.GET and request.GET['salesman'] != '':
            transactions = transactions.filter(client__salesman__id=request.GET['salesman'])

        if 'beginDate' in request.GET and request.GET['beginDate'] != '':
            requestBeginDate = datetime.strptime(request.GET['beginDate'], '%Y-%m-%d').date()
            transactions = transactions.filter(date__gte=requestBeginDate)
        else:
            requestBeginDate = ''

        if 'endDate' in request.GET and request.GET['endDate'] != '':
            requestEndDate = datetime.strptime(request.GET['endDate'], '%Y-%m-%d').date()
            transactions = transactions.filter(date__lte=requestEndDate)

        data = {}

        # yearWise Data
        yearMin = date.today().year
        yearMax = 1900
        beginDate = date.today()
        endDate = datetime.strptime('1900-01-01', '%Y-%m-%d').date()

        prediction = {}
        volume = {}
        tk = {}
        label = []

        for t in transactions:
            year = t.date.year
            if year in tk:
                tk[year] += t.amount
            else:
                tk[year] = t.amount

            if year in volume:
                volume[year] += t.volume
            else:
                volume[year] = t.volume

            yearMin = min(yearMin, t.date.year)
            yearMax = max(yearMax, t.date.year)
            beginDate = min(beginDate, t.date)
            endDate = max(endDate, t.date)

        for i in range(yearMin, yearMax + 3):
            label.append(i)
            if i not in volume:
                volume[i] = 0
                tk[i] = 0
            prediction[i] = volume[i]

        for i in range(yearMax + 1, yearMax + 3):
            if i - yearMin >= 3:
                prediction[i] = self.getPrediction3(prediction[i - 1], prediction[i - 2], prediction[i - 3])
            elif i - yearMin >= 2:
                prediction[i] = self.getPrediction2(prediction[i - 1], prediction[i - 2])
            elif i - yearMin >= 1:
                prediction[i] = prediction[i - 1]
            else:
                prediction[i] = 0

        data['yearWise'] = {
            'label': label,
            'volume': [volume[i] for i in range(yearMin, yearMax + 3)],
            'tk': [tk[i] for i in range(yearMin, yearMax + 3)],
            'prediction': [prediction[i] for i in range(yearMin, yearMax + 3)]
        }

        # monthWise Data
        if requestBeginDate == '':
            beginDateForMonth = max(beginDate, endDate.replace(year=endDate.year - 1))
            beginDateForMonth = beginDateForMonth.replace(day=1)
        else:
            beginDateForMonth = beginDate

        endDateForMonth = self.addMonthsToDate(endDate, 1)

        if beginDateForMonth.year == endDateForMonth.year:
            monthCount = endDateForMonth.month - beginDateForMonth.month
        else:
            monthCount = (
                                 endDateForMonth.year - beginDateForMonth.year) * 12 - beginDateForMonth.month + endDateForMonth.month
        monthCount = max(monthCount, 0)

        prediction = {}
        volume = {}
        tk = {}
        label = []

        for t in transactions:
            if t.date < beginDateForMonth or t.date >= endDateForMonth:
                continue
            key = t.date.strftime('%b %y')

            if key in tk:
                tk[key] += t.amount
            else:
                tk[key] = t.amount

            if key in volume:
                volume[key] += t.volume
            else:
                volume[key] = t.volume

        for i in range(0, monthCount + 2):
            key = self.addMonthsToDate(beginDateForMonth, i).strftime('%b %y')
            label.append(key)
            if key not in volume:
                volume[key] = 0
                tk[key] = 0
            prediction[key] = volume[key]

        for i in range(monthCount - 3, monthCount - 1):
            key = self.addMonthsToDate(beginDateForMonth, i + 3).strftime('%b %y')
            if i + 2 >= 0:
                oneMonthBeforeKey = self.addMonthsToDate(beginDateForMonth, i + 2).strftime('%b %y')
                prediction[key] = prediction[oneMonthBeforeKey]
            if i + 1 >= 0:
                twoMonthBeforeKey = self.addMonthsToDate(beginDateForMonth, i + 1).strftime('%b %y')
                prediction[key] = self.getPrediction2(
                    prediction[oneMonthBeforeKey],
                    prediction[twoMonthBeforeKey]
                )
            if i >= 0:
                threeMonthBeforeKey = self.addMonthsToDate(beginDateForMonth, i).strftime('%b %y')
                prediction[key] = self.getPrediction3(
                    prediction[oneMonthBeforeKey],
                    prediction[twoMonthBeforeKey],
                    prediction[threeMonthBeforeKey]
                )

        data['monthWise'] = {
            'label': label,
            'volume': [],
            'tk': [],
            'prediction': []
        }

        for i in range(0, monthCount + 2):
            data['monthWise']['volume'].append(volume[label[i]])
            data['monthWise']['tk'].append(tk[label[i]])
            data['monthWise']['prediction'].append(prediction[label[i]])

        # dayWise Data
        if requestBeginDate == '':
            beginDateForDay = max(beginDate, endDate - timedelta(days=30))
        else:
            beginDateForDay = beginDate

        endDateForDay = endDate + timedelta(days=1)

        dayCount = (endDateForDay - beginDateForDay).days

        prediction = {}
        volume = {}
        tk = {}
        label = []

        for t in transactions:
            if t.date < beginDateForDay or t.date >= endDateForDay:
                continue
            key = t.date.strftime('%b %d, %y')
            if key in tk:
                tk[key] += t.amount
            else:
                tk[key] = t.amount

            if key in volume:
                volume[key] += t.volume
            else:
                volume[key] = t.volume

        for i in range(0, dayCount + 2):
            key = (beginDateForDay + timedelta(days=i)).strftime('%b %d, %y')
            label.append(key)
            if key not in volume:
                volume[key] = 0
                tk[key] = 0
            prediction[key] = volume[key]

        for i in range(dayCount - 3, dayCount - 1):
            key = (beginDateForDay + timedelta(days=i + 3)).strftime('%b %d, %y')
            if i + 2 >= 0:
                oneDayBeforeKey = (beginDateForDay + timedelta(days=i + 2)).strftime('%b %d, %y')
                prediction[key] = prediction[oneDayBeforeKey]
            if i + 1 >= 0:
                twoDaysBeforeKey = (beginDateForDay + timedelta(days=i + 1)).strftime('%b %d, %y')
                prediction[key] = self.getPrediction2(
                    prediction[oneDayBeforeKey],
                    prediction[twoDaysBeforeKey]
                )
            if i >= 0:
                threeDaysBeforeKey = (beginDateForDay + timedelta(days=i)).strftime('%b %d, %y')
                prediction[key] = self.getPrediction3(
                    prediction[oneDayBeforeKey],
                    prediction[twoDaysBeforeKey],
                    prediction[threeDaysBeforeKey]
                )

        data['dayWise'] = {
            'label': label,
            'volume': [],
            'tk': [],
            'prediction': []
        }

        for i in range(0, dayCount + 2):
            data['dayWise']['volume'].append(volume[label[i]])
            data['dayWise']['tk'].append(tk[label[i]])
            data['dayWise']['prediction'].append(prediction[label[i]])

        return Response(data)


class Percentile(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        p_type = request.GET['modelName']
        qs = PercentileInfo.objects.filter(p_type=p_type).order_by('number')
        total = 0
        for x in qs:
            total += x.amount

        label = []
        for i in range(1, 100, 20): label.append(str(i) + "-" + str(i + 19) + '%')
        data = {
            'label': label,
            'data': [(x.amount * 100 / total) for x in qs]
        }
        return Response(data)


def clients(request):
    today = date.today()
    qs = Transaction.objects.all()
    qyear = qs.filter(voucher__date__gte=today.replace(month=1, day=1), voucher__date__lte=today)
    qmonth = qs.filter(voucher__date__gte=today - timedelta(days=30), voucher__date__lte=today)
    qweek = qs.filter(voucher__date__gte=today - timedelta(days=7), voucher__date__lte=today)

    # begin & end
    weekBegin = today - timedelta(days=6)
    weekEnd = today
    monthBegin = today - timedelta(days=29)
    monthEnd = today
    yearBegin = today.replace(month=1, day=1)
    yearEnd = today
    context = {
        'weekBegin': weekBegin,
        'weekEnd': weekEnd,
        'monthBegin': monthBegin,
        'monthEnd': monthEnd,
        'yearBegin': yearBegin,
        'yearEnd': yearEnd,
    }
    return render(request, 'main/clients.html', context)


class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        populate()

        paginator = Paginator(pairs, pageint)
        page = kwargs.get('page_id', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except EmptyPage:
            users = paginator.page(paginator.num_pages)

        data = {
            'labels': [x.id for x, y in users],
            'data': [y for x, y in users],

        }
        return Response(data)


class Check(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        print(render(request, 'main/base.html'))
        data = {
            'labels': [1, 2, 3, 4],
            'data': [pageint, 20, 30, 40],
            'div': render_to_string('main/index.html', ),

        }
        return Response(data)


class LatestPurchase(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):

        page = kwargs.get('page', 1)
        qs = Transaction.objects.all()
        latest = qs.order_by('-voucher__date')
        paginator = Paginator(latest, pageint)
        page = kwargs.get('page', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except EmptyPage:
            users = paginator.page(paginator.num_pages)

        print(users)
        data = {
            'LatestPurchase': render_to_string('main/includes/transactiontable.html', {'transaction': users, }),
            'latestPaginator': render_to_string('main/includes/Paginator.html', {'page': users, 'page_range': pg})

        }
        return Response(data)


class LatestClient(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        today = date.today()
        table = kwargs['type']
        if (table == None):
            return None

        query = []
        if table == 'week':
            query = Transaction.objects.filter(date__gte=today - timedelta(days=7), date__lte=today)
        elif table == 'month':
            query = Transaction.objects.filter(date__gte=today - timedelta(days=30), date__lte=today)
        else:
            query = Transaction.objects.filter(date__gte=today.replace(month=1, day=1), date__lte=today)
        query = query.filter(t_type='PURCHASE')

        for c in Client.objects.all(): dic[c] = 0
        for i in query: dic[i.client] += i.amount
        serial = sorted(Client.objects.all(), key=cmp, reverse=True)
        yearTable = [(i, dic[i]) for i in serial]
        yearData = [dic[i] for i in serial]

        paginator = Paginator(yearTable, pageint)
        page = kwargs.get('page', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            pageYear = paginator.page(page)
        except PageNotAnInteger:
            pageYear = paginator.page(1)
        except EmptyPage:
            pageYear = paginator.page(paginator.num_pages)

        data = {
            'Table': render_to_string('main/includes/clientTable.html', {'page': pageYear}),
            'Data': yearData[pageYear.start_index() - 1: pageYear.end_index()],
            'Labels': [' '] * (pageYear.end_index() - pageYear.start_index() + 1),
            'Paginator': render_to_string('main/includes/Paginator.html', {'page': pageYear, 'page_range': pg})

        }

        return Response(data)


class LoadDefaultClients(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        today = date.today()
        qs = Transaction.objects.all().filter(t_type='PURCHASE')
        qyear = qs.filter(date__gte=today.replace(month=1, day=1), voucher__date__lte=today)
        qmonth = qs.filter(date__gte=today - timedelta(days=30), voucher__date__lte=today)
        qweek = qs.filter(voucher__date__gte=today - timedelta(days=7), voucher__date__lte=today)

        for c in Client.objects.all(): dic[c] = 0
        for i in qyear: dic[i.client] += i.amount
        serial = sorted(Client.objects.all(), key=cmp, reverse=True)
        yearTable = [(i, dic[i]) for i in serial]
        yearData = [dic[i] for i in serial]

        paginator = Paginator(yearTable, pageint)
        page = kwargs.get('page', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            pageYear = paginator.page(page)
        except PageNotAnInteger:
            pageYear = paginator.page(1)
        except EmptyPage:
            pageYear = paginator.page(paginator.num_pages)

        for c in Client.objects.all(): dic[c] = 0
        for i in qweek: dic[i.client] += i.amount
        serial = sorted(Client.objects.all(), key=cmp, reverse=True)
        weekTable = [(i, dic[i]) for i in serial]
        weekData = [dic[i] for i in serial]

        paginator = Paginator(weekTable, pageint)
        page = kwargs.get('page', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            pageWeek = paginator.page(page)
        except PageNotAnInteger:
            pageWeek = paginator.page(1)
        except EmptyPage:
            pageWeek = paginator.page(paginator.num_pages)

        for c in Client.objects.all(): dic[c] = 0
        for i in qmonth: dic[i.client] += i.amount
        serial = sorted(Client.objects.all(), key=cmp, reverse=True)
        monthTable = [(i, dic[i]) for i in serial]
        monthData = [dic[i] for i in serial]

        paginator = Paginator(monthTable, pageint)
        page = kwargs.get('page', 1)
        pg = proper_paginate(paginator, int(page))

        try:
            pagemonth = paginator.page(page)
        except PageNotAnInteger:
            pagemonth = paginator.page(1)
        except EmptyPage:
            pagemonth = paginator.page(paginator.num_pages)

        data = {
            'yearTable': render_to_string('main/includes/clientTable.html', {'page': pageYear}),
            'yearData': yearData[pageYear.start_index() - 1: pageYear.end_index()],
            'yearLabels': [' '] * (pageYear.end_index() - pageYear.start_index() + 1),
            'yearPaginator': render_to_string('main/includes/Paginator.html', {'page': pageYear, 'page_range': pg}),

            'weekTable': render_to_string('main/includes/clientTable.html', {'page': pageWeek}),
            'weekData': weekData[pageWeek.start_index() - 1: pageWeek.end_index()],
            'weekLabels': [' '] * (pageWeek.end_index() - pageWeek.start_index() + 1),
            'weekPaginator': render_to_string('main/includes/Paginator.html', {'page': pageWeek, 'page_range': pg}),

            'monthTable': render_to_string('main/includes/clientTable.html', {'page': pagemonth}),
            'monthData': monthData[pagemonth.start_index() - 1: pagemonth.end_index()],
            'monthLabels': [' '] * (pagemonth.end_index() - pagemonth.start_index() + 1),
            'monthPaginator': render_to_string('main/includes/Paginator.html', {'page': pagemonth, 'page_range': pg}),

        }

        return Response(data)


def uploadFile(request):
    if request.method == 'POST' and 'dataFile' in request.FILES and 'fileType' in request.POST:
        dataFile = request.FILES['dataFile']
        fileType = request.POST['fileType']
        fs = FileSystemStorage()
        fs.save(fileType + '/' + dataFile.name, dataFile)
    return render(request, 'main/uploadFile.html')


def deleteData(request):
    if request.method == 'POST' and 'accept' in request.POST:
        if request.POST['accept'] == 'yes':
            print("DELETING")
            fs = FileSystemStorage()
            fs.delete('return')
            # SalesMan.objects.all().delete()
            # Region.objects.all().delete()
            # Client.objects.all().delete()
            # Product.objects.all().delete()
            # Transaction.objects.all().delete()
            # PercentileInfo.objects.all().delete()
    return render(request, 'main/deleteData.html')


def loginView(request):
    if (request.method == 'GET'):
        return render(request, 'main/login.html', )

    print(request.POST)
    if (request.method == 'POST'):
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')

    return redirect('login')


def logoutView(request):
    logout(request)
    return redirect('login')
