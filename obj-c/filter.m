+ (void)set1dRawAndFilteredValueWithInput:(NSMutableArray *) sensorHistory withFilterParam:(NSArray*) filterParam forRawData:(NSMutableArray *) rawData forFilteredData:(NSMutableArray *) filteredData
{

    int filterLength=[[filterParam objectAtIndex:0] intValue];
    double samplingFreq = [[filterParam objectAtIndex:3] doubleValue];
    double firstFreqCutoff = [[filterParam objectAtIndex:1] doubleValue];
    double secondFreqCutoff = [[filterParam objectAtIndex:2] doubleValue];
    double* weights=new double[filterLength];
    int M = filterLength-1;
    double ft1 = firstFreqCutoff/samplingFreq;
    double ft2 = secondFreqCutoff/samplingFreq;
    for (int i=0; i<filterLength; i++) {
        if(i!=M/2){
            weights[i]= sin(2*M_PI*ft2*(i-M/2))/(M_PI*(i-M/2))-sin(2*M_PI*ft1*(i-M/2))/(M_PI*(i-M/2));
        }
        else{
            weights[i] =  2*(ft2-ft1);
        }
        weights[i] = weights[i]*(0.54 - 0.46*cos(2*M_PI*i/M));
    }
    
    double outputSignal = 0;
    for (int i=0; i<[sensorHistory count]; i++) {
        E201dDataPoint* dataPoint = [sensorHistory objectAtIndex:i];
        outputSignal += dataPoint.value*weights[i];
    }
    E201dDataPoint* sourcePoint = [sensorHistory objectAtIndex:M/2];
    E201dDataPoint* rawPoint = [E201dDataPoint copyDataPoint:sourcePoint];
    [rawData addObject:rawPoint];
    if([rawData count]>maxSensorHistoryStored){
        [rawData removeObjectAtIndex:0];
    }
    E201dDataPoint* filteredPoint = [E201dDataPoint dataPointFromDouble:outputSignal];
    //careful not setting timeStamp for filteredData...could be useful later on
    [filteredData addObject:filteredPoint];
    if([filteredData count]>maxSensorHistoryStored){
        [filteredData removeObjectAtIndex:0];
    }
    
}
