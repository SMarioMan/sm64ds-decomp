"""Read-only native input cadence measurements from the stock-core frontend.

These are emulated DS VBlank intervals, not host wall-clock FPS or hardware
acceptance. Compare equivalent scenes and keep paused samples separate.
"""
import json


def capture_performance(ds, name):
    lines=ds.command('performance')
    rows={}
    for line in lines:
        fields=line.split()
        if not fields or fields[0] not in ('PERFORMANCE','CADENCE','PHASES','GEOMETRY','PROCESS_PHASES','PROCESS_ACTORS'):continue
        key=tuple(map(int,fields[1:5]))
        row=rows.setdefault(key,dict(zip(('console','wireless','level','paused'),key)))
        if fields[0]=='PERFORMANCE':
            row.update(zip(('observations','intervals','vblanks','longestVblanks',
                            'tickDiscontinuities'),map(int,fields[5:])))
        elif fields[0]=='GEOMETRY':
            row.update(zip(('maxRenderedPolygons','maxBuildingPolygons','maxBuildingVertices',
                            'geometryOverflowFlagSamples','geometryOverflowFlagRises'),map(int,fields[5:])))
        else:
            row[{'CADENCE':'cadenceHistogram','PHASES':'phaseObservations',
                 'PROCESS_PHASES':'processPhaseObservations','PROCESS_ACTORS':'processActorObservations'}[fields[0]]]={
                int(bin):int(count) for bin,count in (item.split(':') for item in fields[5:])}
    result={'measurement':'emulated-sdk-vblanks-per-native-outgoing-input-tick',
            'hardwareAcceptance':False,'renderedFpsMeasured':False,
            'initializingScenesExcluded':True,'loadingFlagExcluded':True,
            'overflowHistogramBin':256,'rows':list(rows.values())}
    for row in result['rows']:
        if 'processActorObservations' in row:
            row['processActors']=[{'phase':key>>16 if key>=65536 else key//354,
                'actorID':key&65535 if key>=65536 else key%354,'observations':count}
                for key,count in sorted(row.pop('processActorObservations').items())]
        intervals=row['intervals']
        histogram=row['cadenceHistogram']
        if sum(histogram.values())!=intervals:
            raise RuntimeError('Incomplete native cadence histogram')
        row['meanVblanksPerInputTick']=row['vblanks']/intervals if intervals else None
        row['unclassifiedPhaseObservations']=row['observations']-sum(row['phaseObservations'].values())
        row['intervalsOverTwoVblanks']=sum(count for bin,count in histogram.items() if bin>2)
        for percentile in (50,95,99):
            cumulative=0
            row[f'p{percentile}Vblanks']=None
            for bin,count in sorted(histogram.items()):
                cumulative+=count
                if intervals and cumulative*100>=intervals*percentile:
                    row[f'p{percentile}Vblanks']=bin
                    break
    (ds.output/(name+'-performance.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result
