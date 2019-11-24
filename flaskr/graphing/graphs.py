import numpy as np
import os
import zipfile
import seaborn
import io
import base64
import pandas as pd
import time
from flask import current_app
import matplotlib
matplotlib.use('Agg')

from matplotlib import pyplot as plt
from flaskr.model.helpers.functions import saveImage, get_unique_group
from flaskr.model.helpers.buildfunctions import get_collection
from flaskr.framework.model.request.response import Response


class Grapher:
    def __init__(
            self,
            dataset_id: str,
            customtitle: str = '',
            time: list = None
    ):
        self.dataset_id = dataset_id
        self.customtitle = customtitle
        self.time = time
        self.data = {}
        self.zip = None

    def execute(self):
        self.setGraphSettings()
        try:
            os.mkdir(os.path.join(current_app.config['IMAGE_FOLDER'], 'graphs'))
        except OSError:
            pass

        self.zip = zipfile.ZipFile('graphs.zip', 'w')

        df = pd.DataFrame(columns=['index', 'triplicate', 'group', 'label', 'variable', 'value'])
        Headers = []
        Groups = []
        tmestart = time.time()
        for wellindex, well in enumerate(get_collection(self)):
            if not well.is_valid():
                continue
            base = dict(index=wellindex, triplicate=well.get_triplicate(), group=well.get_group(),
                        label=well.get_label())
            for idx, item in enumerate(well.get_inflections()):
                base['variable'] = "Inflection " + str(idx)
                base['value'] = item
                df = df.append(base, ignore_index=True)
                """
            for idx, item in enumerate(well.get_inflectionrfus()):
                base['variable'] = "Inflection RFU " + str(idx)
                base['value'] = item
                df = df.append(base, ignore_index=True)
            for idx, item in enumerate(well.get_percentdiffs()):
                base['variable'] = "Percent Diff " + str(idx)
                base['value'] = item
                df = df.append(base, ignore_index=True)
                """
            Headers.append(well.get_label())
            Groups.append(well.get_group())
        print(time.time() - tmestart)

        # Groups = list(map(lambda d: d[1]['group'], self.data.items()))
        # Headers = getGroupHeaders(list(map(lambda d: d[1]['label'], self.data.items())))

        # outputdf = pd.DataFrame(dict(index=list(self.data.keys()),
        #                              triplicate=[value['triplicate'] for value in self.data.values()],
        #                              group=[value['group'] for value in self.data.values()],
        #                              label=[value['label'] for value in self.data.values()],
        #                              inflection1=[value['inflections'][0] for value in self.data.values()],
        #                              inflection2=[value['inflections'][1] if len(value['inflections']) == 4 else 0
        #                                           for value in self.data.values()],
        #                              inflection3=[value['inflections'][2] if len(value['inflections']) == 4 else
        #                                           value['inflections'][1] if len(value['inflections']) == 2 else 0
        #                                           for value in self.data.values()],
        #                              inflection4=[value['inflections'][3] if len(value['inflections']) == 4 else 0
        #                                           for value in self.data.values()]))

        # averagedf = pd.DataFrame(dict(label=[value['label'] for value in self.data.values()],
        #                              group=[value['group'] for value in self.data.values()],
        #                              inflection1=[value['percentdiffs'][1][0] if value.get('percentdiffs')
        #                                           else 0 for value in self.data.values()],
        #                              inflection2=[value['percentdiffs'][1][1] if value.get('percentdiffs')
        #                                           else 0 for value in self.data.values()],
        #                              inflection3=[value['percentdiffs'][1][2] if value.get('percentdiffs')
        #                                           else 0 for value in self.data.values()],
        #                              inflection4=[value['percentdiffs'][1][3] if value.get('percentdiffs')
        #                                           else 0 for value in self.data.values()]))
        # averagedf = averagedf.melt(id_vars=['label', 'group'], var_name='inflection')
        # averagedf = averagedf[(averagedf != 'err')]
        # averagedf = averagedf.dropna()

        # datadf = pd.DataFrame(columns=['index', 'group', 'triplicate', 'time', 'value'])
        # for well in self.data.keys():
        #     tripdf = pd.DataFrame(columns=['index', 'group', 'triplicate', 'value'])
        #     tripdf['index'] = [well for i in range(len(self.data[well]['Values']))]
        #     tripdf['group'] = [self.data[well]['group'] for i in range(len(self.data[well]['RFUs']))]
        #     tripdf['triplicate'] = [self.data[well]['label'] for i in range(len(self.data[well]['RFUs']))]
        #     tripdf['value'] = self.data[well]['RFUs']
        #     tripdf.insert(4, 'time', [t / 60 for t in self.time])
        #     datadf = datadf.append(tripdf, sort=True)
        pics = []
        pics = self.InflectionGraphByGroup(max(Groups), get_unique_group(Headers), df)
        # self.RFUIndividualGraphsByGroup(max(Groups), datadf)
        # self.RFUAverageGraphsByGroup(max(Groups), datadf)
        # self.percentGraphs(max(Groups), averagedf)

        # self.InflectionGraphsByNumber(getUnique(Headers), outputdf)
        # self.RFUAllGraphs(datadf.sort_values(['index']))

        # return Response(True, 'Graphs created successfully')
        return pics

    def InflectionGraphByGroup(self, groups, headers, df):
        pics = []
        for group in range(1, groups+1):
            subinf = df[(df['group'] == group)].sort_values(['index', 'triplicate'])
            indplt = seaborn.swarmplot(x="variable", y="value", hue="label", data=subinf, dodge=True, marker='o',
                                       s=2.6, edgecolor='black', linewidth=.6)
            indplt.set(xticklabels=['Inflection 1', 'Inflection 2', 'Inflection 3', 'Inflection 4'])
            box = plt.gca().get_position()
            plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
            legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
            ax = plt.gca().add_artist(legend1)
            plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label) for idx, label in enumerate(headers)],
                       bbox_to_anchor=(1, .1), loc='lower left')
            plt.xlabel('')
            plt.ylabel('Time (Min)')
            plt.title('Inflections_' + str(group), fontsize=14)
            sio = io.BytesIO()
            plt.savefig(sio, format='png')
            plt.close()
            pics.append(base64.b64encode(sio.getvalue()).decode('utf-8').replace('\n', ''))
        return pics

    def InflectionGraphsByNumber(self, headers, df):
        gd = df.sort_values(by=['triplicate', 'group'], ascending=True)
        gd['triplicateIndex'] = int(gd['group'].max())*(gd['triplicate'] % 8)+gd['group']
        gd['label'] = [x[:-2] for x in gd['label']]
        gd = gd.sort_values(by=['triplicateIndex', 'index', 'triplicate', 'group'], ascending=True)
        numGroups = int(gd['group'].max())
        xaxis = [i + 1 for i in range(numGroups)]
        xaxis = xaxis * int(len(df['index']) / numGroups)
        for inf in range(4):
            fig = plt.figure()
            indplt = seaborn.swarmplot(x="triplicateIndex", y='inflection' + str(inf + 1), hue="label", data=gd,
                                       marker='o', s=2.6, edgecolor='black', linewidth=.6)
            indplt.set(xticklabels=xaxis)
            plt.ylabel('Time (Min)')
            plt.xlabel('Group Number')
            box = plt.gca().get_position()
            plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
            legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left')
            ax = plt.gca().add_artist(legend1)
            plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label) for idx, label in enumerate(headers)],
                       bbox_to_anchor=(1, .1), loc='lower left')
            saveImage(self, plt, 'Inflection' + str(inf + 1))

    def RFUIndividualGraphsByGroup(self, groups, df):
        for group in range(1, groups+1):
            fig = plt.figure()
            seaborn.lineplot(x='time', y='value', hue='triplicate', units='index', estimator=None, data=df[df['group'] == group],
                             linewidth=.7)
            plt.ylabel('RFU')
            plt.xlabel('Time (Min)')
            saveImage(self, plt, 'Individuals_' + str(group))

    def RFUAverageGraphsByGroup(self, groups, df):
        for group in range(1, groups+1):
            fig = plt.figure()
            groupdf = df[df['group'] == group]
            for triplicate in getUnique([welllabel['label'] for welllabel in self.data.values()]):
                if int(triplicate[-1]) == group:
                    subdf = groupdf[groupdf['triplicate'] == triplicate]
                    seaborn.lineplot(subdf['time'], subdf.mean(1), label=triplicate, linewidth=.7)
            plt.ylabel('RFU')
            plt.xlabel('Time (Min)')
            saveImage(self, plt, 'Averages_' + str(group))

    def RFUAllGraphs(self, df):
        fig = plt.figure()
        manualcolors = ["gray", "darkgreen", "cyan", "gold", "dodgerblue", "red", "lime", "magenta"]
        seaborn.lineplot(x='time', y='value', hue='group', units='index', estimator=None, data=df,
                         palette=manualcolors[-np.max(df['group']):], linewidth=.7)  # hue='group', units='triplicate'
        plt.ylabel('RFU')
        plt.xlabel('Time (Min)')
        saveImage(self, plt, 'Averages_All')

    def percentGraphs(self, groups, df):
        for group in range(1, groups+1):
            fig = plt.figure()
            subpc = df[(df['group'] == group)].sort_values(['inflection'])
            if not subpc.empty:
                indplt = seaborn.swarmplot(x='label', y="value", hue="label", data=subpc, dodge=True, marker='o',
                                           s=2.6, edgecolor='black', linewidth=.6)
                indplt.set(xticklabels='')
                box = plt.gca().get_position()
                plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
                plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
                plt.xlabel('')
                plt.ylabel('Percent Difference from Control')
                saveImage(self, plt, 'PercentDiff_' + str(group))


    def setGraphSettings(self):
        params = {'legend.fontsize': 5,
                  'legend.loc': 'best',
                  'legend.framealpha': 0.5,
                  'figure.dpi': 250,
                  'legend.handlelength': .8,
                  'legend.markerscale': .4,
                  'legend.labelspacing': .4,
                  'font.size': 8}
        plt.rcParams.update(params)
        manualcolors = ["gray", "darkgreen", "cyan", "gold", "dodgerblue", "red", "lime", "magenta"]
        seaborn.set_palette(manualcolors)




