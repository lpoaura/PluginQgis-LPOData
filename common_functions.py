# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : common_functions.py
        -------------------
        Date                 : 2020-04-16
        Copyright            : (C) 2020 by Elsa Guilley (LPO AuRA)
        Email                : lpo-aura@lpo.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Elsa Guilley (LPO AuRA)'
__date__ = '2020-04-16'
__copyright__ = '(C) 2020 by Elsa Guilley (LPO AuRA)'

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.utils import iface
from qgis.gui import QgsMessageBar

from qgis.core import (QgsWkbTypes,
                       QgsProcessingException,
                       Qgis)
import processing


def simplify_name(string):
    """
    Simplify a layer name written by the user.
    """
    translation_table = str.maketrans(
        'àâäéèêëîïôöùûüŷÿç~- ',
        'aaaeeeeiioouuuyyc___',
        "2&'([{|}])`^\/@+-=*°$£%§#.?!;:<>"
    )
    return string.lower().translate(translation_table)

def check_layer_geometry(layer):
    """
    Check if the input vector layer is a polygon layer.
    """
    if QgsWkbTypes.displayString(layer.wkbType()) not in ['Polygon', 'MultiPolygon']:
        iface.messageBar().pushMessage("Erreur", "La zone d'étude fournie n'est pas valide ! Veuillez sélectionner une couche vecteur de type POLYGONE.", level=Qgis.Critical, duration=10)
        raise QgsProcessingException("La zone d'étude fournie n'est pas valide ! Veuillez sélectionner une couche vecteur de type POLYGONE.")
    return None

def check_layer_is_valid(feedback, layer):
    """
    Check if the input vector layer is valid.
    """
    if not layer.isValid():
        raise QgsProcessingException(""""La couche PostGIS chargée n'est pas valide !
            Checkez les logs de PostGIS pour visualiser les messages d'erreur.""")
    else:
        #iface.messageBar().pushMessage("Info", "La couche PostGIS demandée est valide, la requête SQL a été exécutée avec succès !", level=Qgis.Info, duration=10)
        feedback.pushInfo("La couche PostGIS demandée est valide, la requête SQL a été exécutée avec succès !")
    return None

def set_features(layer):
    """
    Retrieve the selected features of the input vector layer.
    """
    if len(layer.selectedFeatures()) > 0:
        selection = layer.selectedFeatures()
    else:
        # If there is no feature selected, get all of them
        selection = layer.getFeatures() 
    return selection

def construct_sql_array_polygons(layer):
    """
    Construct the sql array containing the input vector layer's features geometry.
    """
    # Initialization of the sql array containing the study area's features geometry
    array_polygons = "array["
    # For each entity in the study area...
    for feature in set_features(layer):
        # Retrieve the geometry
        area = feature.geometry() # QgsGeometry object
        # Retrieve the geometry type (single or multiple)
        geomSingleType = QgsWkbTypes.isSingleType(area.wkbType())
        # Increment the sql array
        if geomSingleType:
            array_polygons += "ST_PolygonFromText('{}', 2154), ".format(area.asWkt())
        else:
            array_polygons += "ST_MPolyFromText('{}', 2154), ".format(area.asWkt())
    # Remove the last "," in the sql array which is useless, and end the array
    array_polygons = array_polygons[:len(array_polygons)-2] + "]"
    return array_polygons

def load_layer(context, layer):
    """
    Load a layer in the current project.
    """
    root = context.project().layerTreeRoot()
    plugin_lpo_group = root.findGroup('Résultats plugin LPO')
    if not plugin_lpo_group:
        plugin_lpo_group = root.insertGroup(0, 'Résultats plugin LPO')
    context.project().addMapLayers([layer], False)
    plugin_lpo_group.addLayer(layer)
    ### Variant
    # context.temporaryLayerStore().addMapLayer(layer)
    # context.addLayerToLoadOnCompletion(
    #     layer.id(),
    #     QgsProcessingContext.LayerDetails("Données d'observations", context.project(), self.OUTPUT)
    # )

def execute_sql_queries(context, feedback, connection, queries):
    """
    Execute severals sql queries.
    """
    for query in queries:
        processing.run(
            'qgis:postgisexecutesql',
            {
                'DATABASE': connection,
                'SQL': query
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback
        )
    feedback.pushInfo('Requête SQL exécutée avec succès !')
    return None