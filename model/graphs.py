import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn
import pandas as pd
from model.functions import saveImage, getUnique, getGroupHeaders, getTriplicateIndexes
from flask import flash


class Grapher:
    def __init__(
            self,
            paths: dict = None,
            customtitle: str = '',
            data=None,
            errors=None,
            time: list = None
    ):
        self.paths = paths
        self.customtitle = customtitle
        self.data = data
        self.errors = errors
        self.time = time

    def execute(self):
        self.setGraphSettings()
        try:
            os.mkdir(os.path.join(self.paths['output'], 'graphs'))
        except OSError:
            pass

        Groups = list(map(lambda d: d[1]['Group'], self.data.items()))
        Headers = getGroupHeaders(list(map(lambda d: d[1]['Label'], self.data.items())))

        outputdf = pd.DataFrame(dict(index=list(self.data.keys()),
                                     triplicate=[value['Triplicate'] for value in self.data.values()],
                                     group=[value['Group'] for value in self.data.values()],
                                     label=[value['Label'] for value in self.data.values()],
                                     inflection1=[value['Inflections'][0] for value in self.data.values()],
                                     inflection2=[value['Inflections'][1] if len(value['Inflections']) == 4 else 0
                                                  for value in self.data.values()],
                                     inflection3=[value['Inflections'][2] if len(value['Inflections']) == 4 else
                                                  value['Inflections'][1] if len(value['Inflections']) == 2 else 0
                                                  for value in self.data.values()],
                                     inflection4=[value['Inflections'][3] if len(value['Inflections']) == 4 else 0
                                                  for value in self.data.values()]))

        averagedf = pd.DataFrame(dict(label=[value['Label'] for value in self.data.values()],
                                     group=[value['Group'] for value in self.data.values()],
                                     inflection1=[value['Relative Difference'][1][0] if value.get('Relative Difference')
                                                  else 0 for value in self.data.values()],
                                     inflection2=[value['Relative Difference'][1][1] if value.get('Relative Difference')
                                                  else 0 for value in self.data.values()],
                                     inflection3=[value['Relative Difference'][1][2] if value.get('Relative Difference')
                                                  else 0 for value in self.data.values()],
                                     inflection4=[value['Relative Difference'][1][3] if value.get('Relative Difference')
                                                  else 0 for value in self.data.values()]))
        averagedf = averagedf.melt(id_vars=['label', 'group'], var_name='inflection')
        averagedf = averagedf[(averagedf != 'err')]
        averagedf = averagedf.dropna()

        datadf = pd.DataFrame(columns=['index', 'group', 'triplicate', 'time', 'value'])
        for well in self.data.keys():
            tripdf = pd.DataFrame(columns=['index', 'group', 'triplicate', 'value'])
            tripdf['index'] = [well for i in range(len(self.data[well]['Values']))]
            tripdf['group'] = [self.data[well]['Group'] for i in range(len(self.data[well]['Values']))]
            tripdf['triplicate'] = [self.data[well]['Label'] for i in range(len(self.data[well]['Values']))]
            tripdf['value'] = self.data[well]['Values']
            tripdf.insert(4, 'time', [t / 60 for t in self.time])
            datadf = datadf.append(tripdf, sort=True)


        self.InflectionGraphByGroup(max(Groups), getUnique(Headers), outputdf)
        self.RFUIndividualGraphsByGroup(max(Groups), datadf)
        self.RFUAverageGraphsByGroup(max(Groups), datadf)
        self.percentGraphs(max(Groups), averagedf)

        self.InflectionGraphsByNumber(getUnique(Headers), outputdf)
        self.RFUAllGraphs(datadf.sort_values(['index']))

        return

    def InflectionGraphByGroup(self, groups, headers, df):
        for group in range(1, groups+1):
            idg = df.melt(id_vars=['triplicate', 'group', 'label', 'index'], var_name='inflection')
            idg['inflection'] = idg['inflection'].str.replace(r'inflection', r'').astype('int')
            subinf = idg[(idg['group'] == group)].sort_values(['index', 'inflection', 'triplicate'])
            indplt = seaborn.swarmplot(x="inflection", y="value", hue="label", data=subinf, dodge=True, marker='o',
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
            saveImage(self, plt, 'Inflections_' + str(group))

    def InflectionGraphsByNumber(self, headers, df):
        gd = df.sort_values(by=['triplicate', 'group'], ascending=True)
        gd['triplicateIndex'] = int(gd['group'].max())*(gd['triplicate'] % 8)+gd['group']
        gd['label'] = [x[:-2] for x in gd['label']]
        gd = gd.sort_values(by=['triplicateIndex', 'index', 'triplicate', 'group'], ascending=True)
        numGroups = int(gd['group'].max())
        xaxis = [i + 1 for i in range(numGroups)]
        xaxis = xaxis * int(len(df['index']) / numGroups)
        for inf in range(4):
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
            seaborn.lineplot(x='time', y='value', hue='triplicate', units='index', estimator=None, data=df[df['group'] == group],
                             linewidth=.7)
            plt.ylabel('RFU')
            plt.xlabel('Time (Min)')
            saveImage(self, plt, 'Individuals_' + str(group))

    def RFUAverageGraphsByGroup(self, groups, df):
        for group in range(1, groups+1):
            groupdf = df[df['group'] == group]
            for triplicate in getUnique([welllabel['Label'] for welllabel in self.data.values()]):
                if int(triplicate[-1]) == group:
                    subdf = groupdf[groupdf['triplicate'] == triplicate]
                    seaborn.lineplot(subdf['time'], subdf.mean(1), label=triplicate, linewidth=.7)
            plt.ylabel('RFU')
            plt.xlabel('Time (Min)')
            saveImage(self, plt, 'Averages_' + str(group))

    def RFUAllGraphs(self, df):
        manualcolors = ["gray", "darkgreen", "cyan", "gold", "dodgerblue", "red", "lime", "magenta"]
        seaborn.lineplot(x='time', y='value', hue='group', units='index', estimator=None, data=df,
                         palette=manualcolors[-np.max(df['group']):], linewidth=.7)  # hue='group', units='triplicate'
        plt.ylabel('RFU')
        plt.xlabel('Time (Min)')
        saveImage(self, plt, 'Averages_All')

    def percentGraphs(self, groups, df):
        for group in range(1, groups+1):
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
                  'figure.dpi': 300,
                  'legend.handlelength': .8,
                  'legend.markerscale': .4,
                  'legend.labelspacing': .4,
                  'font.size': 8}
        plt.rcParams.update(params)
        manualcolors = ["gray", "darkgreen", "cyan", "gold", "dodgerblue", "red", "lime", "magenta"]
        seaborn.set_palette(manualcolors)




