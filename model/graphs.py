import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn
import pandas as pd
from model.functions import saveImage, getUniqueKeys, getGroupHeaders
from flask import flash


class Grapher:
    def __init__(
            self,
            path: str = '',
            data=None,
            labels=None,
            output=None,
            averageoutput=None,
            errors=None
    ):
        self.path = path
        self.title = ''
        self.data = data
        self.labeldict = labels
        self.output = output
        self.averageoutput = averageoutput
        self.errors = errors

    def execute(self):
        self.setGraphSettings()
        self.title = os.path.split(self.path)[1][:13]
        self.path = os.path.join(self.path, 'Graphs')
        try:
            os.mkdir(self.path)
        except OSError:
            pass

        Groups = getUniqueKeys([e[1] for e in self.labeldict.values()])
        triplicate = [welllabel[0] for welllabel in self.labeldict.values()]

        groupHeaders = getGroupHeaders([welllabel[0] for welllabel in self.labeldict.values()])

        outputdf = pd.DataFrame(dict(index=list(self.labeldict.keys()),
                                     triplicate=[int(idx % 8) for idx, trip in enumerate(self.labeldict.values())],
                                     group=[int(e[1]) for e in list(self.labeldict.values())],
                                     label=[e[0] for e in self.labeldict.values()],
                                     inflection1=[value['Inflections'][0] for value in self.output.values()],
                                     inflection2=[value['Inflections'][1] for value in self.output.values()],
                                     inflection3=[value['Inflections'][2] for value in self.output.values()],
                                     inflection4=[value['Inflections'][3] for value in self.output.values()]))

        datadf = pd.DataFrame(columns=['index', 'group', 'triplicate', 'time', 'value'])
        for well in self.data.keys():
            if well == 'Time':
                continue
            tripdf = pd.DataFrame(columns=['index', 'group', 'triplicate', 'value'])
            tripdf['index'] = [well for i in range(len(self.data[well]['Values']))]
            tripdf['group'] = [self.data[well]['Group'] for i in range(len(self.data[well]['Values']))]
            tripdf['triplicate'] = [self.data[well]['Label'] for i in range(len(self.data[well]['Values']))]
            tripdf['value'] = self.data[well]['Values']
            tripdf.insert(4, 'time', [t / 60 for t in self.data['Time']])
            datadf = datadf.append(tripdf, sort=True)

        for group in getUniqueKeys([e[1] for e in self.labeldict.values()]):
            self.InflectionGraphByGroup(int(group), groupHeaders, outputdf)
            self.RFUIndividualGraphsByGroup(int(group), datadf)
            self.RFUAverageGraphsByGroup(int(group), datadf)
            flash(str('Graphed ' + group + ' successfully'))

        self.InflectionGraphsByNumber(groupHeaders, outputdf)
        self.RFUAllGraphs(groupHeaders, datadf)
        self.percentGraphs(Groups)
        return

    def InflectionGraphByGroup(self, group, headers, df):
        idg = df.melt(id_vars=['triplicate', 'group', 'label', 'index'], var_name='inflection')
        idg['inflection'] = idg['inflection'].str.replace(r'inflection', r'').astype('int')
        subinf = idg[(idg['group'] == group)].sort_values(['index', 'inflection', 'triplicate'])
        indplt = seaborn.swarmplot(x="inflection", y="value", hue="label", data=subinf, dodge=True, marker='o',
                                   s=2.6, edgecolor='black', linewidth=.6)
        indplt.set(xticklabels=['Inflection 1', 'Inflection 2', 'Inflection 3', 'Inflection 4'])
        # handles, labels = indplt.get_legend_handles_labels()
        # plt.legend(handles=handles[1:], labels=labels[1:])
        # plt.legend(title="Triplicates")
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
        # df = pd.DataFrame(dict(index=IndResult[:, 1],
        #                        triplicate=IndResult[:, 3] % 8,
        #                        group=IndResult[:, 2],
        #                        Triplicates=[triplicateHeaders[int(x % 8)] for x in IndResult[:, 1]],
        #                        inf1=IndResult[:, 4],
        #                        inf2=IndResult[:, 5],
        #                        inf3=IndResult[:, 6],
        #                        inf4=IndResult[:, 7]))
        gd = df.sort_values(by=['triplicate', 'group'], ascending=True)
        gd['triplicateIndex'] = int(gd['group'].max()) * df['triplicate'] + df['group']
        # gd = removeBadWells(badWells,gd,'index')
        numGroups = int(int(gd['group'].max()))
        xaxis = [i + 1 for i in range(numGroups)]
        xaxis = xaxis * int(len(df['index']) / (getUniqueKeys(df['group'])))
        # plt.legend(handles=handles[1:], labels=[label+'-'+group for label,group in zip(labels[1:],groupHeaders)])
        for inf in range(4):
            indplt = seaborn.swarmplot(x="triplicateIndex", y='inf ' + str(inf + 1), hue="Triplicates", data=gd,
                                       marker='o', s=2.6, edgecolor='black', linewidth=.6)
            indplt.set(xticklabels=xaxis)
            # handles, labels = indplt.get_legend_handles_labels()
            # plt.legend(handles=handles[1:], labels=labels[1:])
            plt.ylabel('Time (Min)')
            plt.xlabel('Group Number')
            box = plt.gca().get_position()
            plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
            legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left')
            ax = plt.gca().add_artist(legend1)
            plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label) for idx, label in enumerate(headers)],
                       bbox_to_anchor=(1, .1), loc='lower left')
            saveImage(self, plt, 'Inflection' + str(inf + 1))

    def RFUIndividualGraphsByGroup(self, group, df):
        # idf = pd.DataFrame(columns=['time', 'index', 'value', 'triplicate'])
        # # TODO: create a subdf with the three lines in a triplicate
        # for index, triplicate in enumerate(triplicateHeaders):
        #     if int(triplicate[-1]) == group:
        #         listIndsInTrip = np.where(IndResult[:, 1] == index)
        #         listIndsInTrip = [elem for elem in listIndsInTrip[0] if elem not in badWells]
        #         tripdf = rdf[listIndsInTrip]
        #         tripdf.insert(0, 'time', times / 60)
        #         tripdf = tripdf.melt(id_vars='time', var_name='index')
        #         tripdf['triplicate'] = triplicate
        #         idf = idf.append(tripdf, ignore_index=True, sort=True)
        df = df[df['group'] == group]
        snsplt = seaborn.lineplot(x='time', y='value', hue='triplicate', units='index', estimator=None, data=df,
                                  linewidth=.7)
        handles, labels = snsplt.get_legend_handles_labels()
        plt.legend(handles=handles[1:], labels=labels[1:])
        plt.ylabel('RFU')
        plt.xlabel('Time (Min)')
        saveImage(self, plt, 'Individuals_' + str(group))

    def RFUAverageGraphsByGroup(self, group, df):
        df = df[df['group'] == group]
        for triplicate in getUniqueKeys([welllabel[0] for welllabel in self.labeldict.values()]):
            if int(triplicate[-1]) == group:
                subdf = df[df['triplicate'] == triplicate]
                seaborn.lineplot(subdf['time'], subdf.mean(1), label=triplicate, linewidth=.7)
        plt.ylabel('RFU')
        plt.xlabel('Time (Min)')
        saveImage(self, plt, 'Averages_' + str(group))

    def RFUAllGraphs(self, headers, df):
    #     adf = pd.DataFrame(columns=['triplicate' ,'group' ,'value'])
    #     for group in Groups:
    #         group = int(group)
    #         for index, triplicate in enumerate(getUniqueKeys([welllabel[0] for welllabel in self.labeldict.values()])):
    #             if int(triplicate[-1]) == group:
    #                 listIndsInTrip = np.where(IndResult[: ,1] == index)
    #                 listIndsInTrip = [ elem for elem in listIndsInTrip[0] if elem not in badWells]
    #                 tripdf = pd.DataFrame(dict(value=rdf[listIndsInTrip].mean(1)))
    #                 tripdf['time'] = times / 60
    #                 tripdf['triplicate'] = index
    #                 tripdf['group'] = 'Group  ' + str(group)
    #                 adf = adf.append(tripdf,ignore_index=True,sort=True)
        print(df.head(3))
        snsplt = seaborn.lineplot(x='time', y='value', hue='group', units='triplicate', estimator=None, data=df,
                                  linewidth=.7)
        handles, labels = snsplt.get_legend_handles_labels()
        plt.legend(handles=handles[1:], labels=[label + '- ' + group for label, group in zip(labels[1:], headers)])
        plt.ylabel('RFU')
        plt.xlabel('Time (Min)')
        saveImage(self, plt, 'Averages_All')

    def percentGraphs(self, Groups):
        df = pd.DataFrame(self.averageoutput)
        print(df.head(3))
        df['label'] = [e[0] for e in self.labeldict.values()]
        df['group'] = [int(e[0][-1]) for e in self.labeldict.values()]
        pcdf = df.melt(id_vars=['label', 'group'], var_name='inflection')
        pcdf = pcdf[(pcdf != 'err')]
        pcdf = pcdf.dropna()
        for group in Groups:
            group = int(group)
            title = self.title + 'Inflections%Diff_' + str(group)
            subpc = pcdf[(pcdf['group'] == group)].sort_values(['inflection'])
            if not subpc.empty:
                indplt = seaborn.swarmplot(x='inflection', y="value", hue="label", data=subpc, dodge=True, marker='o',
                                           s=2.6, edgecolor='black', linewidth=.6)
                # numGroups = int(int(gd['group'].max()))
                # xaxis = [i + 1 for i in range(numGroups)]
                # xaxis = xaxis * int(len(df['index']) / (getUniqueKeys(df['group'])))
                # indplt.set(xticklabels=xaxis)
                # handles, labels = indplt.get_legend_handles_labels()
                # plt.legend(handles=handles[1:], labels=labels[1:])
                # plt.legend(title="Triplicates")
                box = plt.gca().get_position()
                plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
                plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
                plt.xlabel('')
                plt.ylabel('Percent Difference from Control')
                saveImage(self, plt, title)

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




