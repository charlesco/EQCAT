var wms_layers = [];
var format_Japan_adm1_0 = new ol.format.GeoJSON();
var features_Japan_adm1_0 = format_Japan_adm1_0.readFeatures(json_Japan_adm1_0, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_Japan_adm1_0 = new ol.source.Vector({
    attributions: [new ol.Attribution({html: '<a href=""></a>'})],
});
jsonSource_Japan_adm1_0.addFeatures(features_Japan_adm1_0);var lyr_Japan_adm1_0 = new ol.layer.Vector({
                declutter: true,
                source:jsonSource_Japan_adm1_0, 
                style: style_Japan_adm1_0,
                title: '<img src="styles/legend/Japan_adm1_0.png" /> Japan_adm1'
            });var format_zone_contours_report_1 = new ol.format.GeoJSON();
var features_zone_contours_report_1 = format_zone_contours_report_1.readFeatures(json_zone_contours_report_1, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_zone_contours_report_1 = new ol.source.Vector({
    attributions: [new ol.Attribution({html: '<a href=""></a>'})],
});
jsonSource_zone_contours_report_1.addFeatures(features_zone_contours_report_1);var lyr_zone_contours_report_1 = new ol.layer.Vector({
                declutter: true,
                source:jsonSource_zone_contours_report_1, 
                style: style_zone_contours_report_1,
                title: '<img src="styles/legend/zone_contours_report_1.png" /> zone_contours_report'
            });var format_subduction_report_2 = new ol.format.GeoJSON();
var features_subduction_report_2 = format_subduction_report_2.readFeatures(json_subduction_report_2, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_subduction_report_2 = new ol.source.Vector({
    attributions: [new ol.Attribution({html: '<a href=""></a>'})],
});
jsonSource_subduction_report_2.addFeatures(features_subduction_report_2);var lyr_subduction_report_2 = new ol.layer.Vector({
                declutter: true,
                source:jsonSource_subduction_report_2, 
                style: style_subduction_report_2,
                title: '<img src="styles/legend/subduction_report_2.png" /> subduction_report'
            });var format_active_faults_report_3 = new ol.format.GeoJSON();
var features_active_faults_report_3 = format_active_faults_report_3.readFeatures(json_active_faults_report_3, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_active_faults_report_3 = new ol.source.Vector({
    attributions: [new ol.Attribution({html: '<a href=""></a>'})],
});
jsonSource_active_faults_report_3.addFeatures(features_active_faults_report_3);var lyr_active_faults_report_3 = new ol.layer.Vector({
                declutter: true,
                source:jsonSource_active_faults_report_3, 
                style: style_active_faults_report_3,
                title: '<img src="styles/legend/active_faults_report_3.png" /> active_faults_report'
            });

lyr_Japan_adm1_0.setVisible(true);lyr_zone_contours_report_1.setVisible(true);lyr_subduction_report_2.setVisible(true);lyr_active_faults_report_3.setVisible(true);
var layersList = [lyr_Japan_adm1_0,lyr_zone_contours_report_1,lyr_subduction_report_2,lyr_active_faults_report_3];
lyr_Japan_adm1_0.set('fieldAliases', {'ID_0': 'ID_0', 'ISO': 'ISO', 'NAME_0': 'NAME_0', 'ID_1': 'ID_1', 'NAME_1': 'NAME_1', 'NL_NAME_1': 'NL_NAME_1', 'VARNAME_1': 'VARNAME_1', 'TYPE_1': 'TYPE_1', 'ENGTYPE_1': 'ENGTYPE_1', });
lyr_zone_contours_report_1.set('fieldAliases', {'Code1': 'Code1', 'Zone': 'Zone', 'Nb Mesh': 'Nb Mesh', 'YearFreq (avr)': 'YearFreq (avr)', 'MinMag (avr)': 'MinMag (avr)', 'b_value (avr)': 'b_value (avr)', 'MaxMag (avr)': 'MaxMag (avr)', });
lyr_subduction_report_2.set('fieldAliases', {'Code': 'Code', 'Process': 'Process', 'Magnitude': 'Magnitude', 'Name': 'Name', });
lyr_active_faults_report_3.set('fieldAliases', {'Code': 'Code', 'Process': 'Process', 'Magnitude': 'Magnitude', 'Name': 'Name', });
lyr_Japan_adm1_0.set('fieldImages', {'ID_0': 'Hidden', 'ISO': 'Hidden', 'NAME_0': 'Hidden', 'ID_1': 'Hidden', 'NAME_1': 'TextEdit', 'NL_NAME_1': 'Hidden', 'VARNAME_1': 'Hidden', 'TYPE_1': 'Hidden', 'ENGTYPE_1': 'Hidden', });
lyr_zone_contours_report_1.set('fieldImages', {'Code1': 'TextEdit', 'Zone': 'TextEdit', 'Nb Mesh': 'TextEdit', 'YearFreq (avr)': 'TextEdit', 'MinMag (avr)': 'TextEdit', 'b_value (avr)': 'TextEdit', 'MaxMag (avr)': 'TextEdit', });
lyr_subduction_report_2.set('fieldImages', {'Code': 'TextEdit', 'Process': 'TextEdit', 'Magnitude': 'TextEdit', 'Name': 'TextEdit', });
lyr_active_faults_report_3.set('fieldImages', {'Code': 'TextEdit', 'Process': 'TextEdit', 'Magnitude': 'TextEdit', 'Name': 'TextEdit', });
lyr_Japan_adm1_0.set('fieldLabels', {'NAME_1': 'no label', });
lyr_zone_contours_report_1.set('fieldLabels', {'Code1': 'inline label', 'Zone': 'inline label', 'Nb Mesh': 'inline label', 'YearFreq (avr)': 'inline label', 'MinMag (avr)': 'inline label', 'b_value (avr)': 'inline label', 'MaxMag (avr)': 'inline label', });
lyr_subduction_report_2.set('fieldLabels', {'Code': 'header label', 'Process': 'inline label', 'Magnitude': 'inline label', 'Name': 'inline label', });
lyr_active_faults_report_3.set('fieldLabels', {'Code': 'header label', 'Process': 'inline label', 'Magnitude': 'inline label', 'Name': 'header label', });
lyr_active_faults_report_3.on('precompose', function(evt) {
    evt.context.globalCompositeOperation = 'normal';
});