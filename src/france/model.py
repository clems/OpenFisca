# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""

from core.systemsf import SystemSf, Prestation
import france.irpp.funcs as ir
import france.pfam.funcs as pf

class Model(SystemSf):
    # variables pour l'ir
    marpac = Prestation(ir._marpac, 'foy')
    celdiv = Prestation(ir._celdiv, 'foy')
    veuf = Prestation(ir._veuf, 'foy')
    jveuf = Prestation(ir._jveuf, 'foy')

    rbg = Prestation(ir._rbg, 'foy', label = u"Revenu brut global")
    rng = Prestation(ir._rng, 'foy', label = u"Revenu net global")
    rni = Prestation(ir._rni, 'foy', label = u"Revenu net imposable")
    
    abat_spe = Prestation(ir._abat_spe, 'foy', label = u"Abattements spéciaux")
    alloc = Prestation(ir._alloc, 'foy', label = u"Allocation familiale pour l'ir")
    deficit_ante = Prestation(ir._deficit_ante, 'foy', label = u"Déficit global antérieur")
    rev_cat = Prestation(ir._rev_cat, 'foy', label = u"Revenus catégoriels")
    nbptr = Prestation(ir._nbptr, 'foy', label = u"Nombre de parts")
    rev_sal = Prestation(ir._rev_sal)
    sal_net = Prestation(ir._sal_net)
    rev_pen = Prestation(ir._rev_pen)
    pen_net = Prestation(ir._pen_net)
    tspr = Prestation(ir._tspr)
    rev_cat_tspr = Prestation(ir._rev_cat_tspr, 'foy', label = u"Revenu catégoriel - Salaires, pensions et rentes")
    rev_cat_rvcm = Prestation(ir._rev_cat_rvcm, 'foy', label = u'Revenu catégoriel - Capitaux')
    rev_cat_rpns = Prestation(ir._rev_cat_rpns, 'foy', label = u'Revenu catégoriel - Rpns')
    rev_cat_rfon = Prestation(ir._rev_cat_rfon, 'foy', label = u'Revenu catégoriel - Foncier')
    rto_net = Prestation(ir._rto_net, 'foy', label = u'Rentes viagère après abattements')
    deficit_rcm = Prestation(ir._deficit_rcm, 'foy', u'Deficit capitaux mobiliers')
    csg_deduc = Prestation(ir._csg_deduc, 'foy', u'Csg déductible')
    
    plus_values = Prestation(ir._plus_values, 'foy')
    ir_brut = Prestation(ir._ir_brut, 'foy')
    nb_pac = Prestation(ir._nb_pac, 'foy')
    nb_adult = Prestation(ir._nb_adult, 'foy')
    ir_plaf_qf = Prestation(ir._ir_plaf_qf, 'foy')
    nat_imp = Prestation(ir._nat_imp, 'foy')
    decote = Prestation(ir._decote, 'foy')
    ip_net = Prestation(ir._ip_net, 'foy')
    iaidrdi = Prestation(ir._iaidrdi, 'foy')
    teicaa = Prestation(ir._teicaa, 'foy')
    cont_rev_loc = Prestation(ir._cont_rev_loc, 'foy')
    iai = Prestation(ir._iai,'foy')


    rev_coll = Prestation(ir._rev_coll, 'foy')
#    alv = Prestation(ir._alv)
    glo = Prestation(ir._glo, 'foy')
    rag  = Prestation(ir._rag)
    ric  = Prestation(ir._ric)
    rac  = Prestation(ir._rac)
    rnc  = Prestation(ir._rnc)
    rpns = Prestation(ir._rpns)
    div  = Prestation(ir._div, 'foy')
    fon  = Prestation(ir._fon, 'foy')
    rpns_mvct = Prestation(ir._rpns_mvct)
    rpns_pvct = Prestation(ir._rpns_pvct)
    rpns_mvlt = Prestation(ir._rpns_mvlt)
    rpns_pvce = Prestation(ir._rpns_pvce)
    
    rev_cap_bar = Prestation(ir._rev_cap_bar, 'foy')
    rev_cap_lib = Prestation(ir._rev_cap_lib, 'foy')
    avf = Prestation(ir._avf, 'foy')
# variables pour les prestations familiales
    etu      = Prestation(pf._etu, label = u"Indicatrice individuelle étudiant")
    biact    = Prestation(pf._biact, 'fam', label = u"Indicatrice de biactivité")
    concub   = Prestation(pf._concub, 'fam', label = u"Indicatrice de vie en couple") 
    nb_par   = Prestation(pf._nb_par, 'fam', label = u"Nombre de parents")
    
    rpns_fam = Prestation(pf._tspr_fam, 'fam', label = u"Traitements, salaires, pensions et rentes de la famille")
    tspr_fam = Prestation(pf._rpns_fam, 'fam', label = u"Revenus des personnes non salariés de la famille")
    rst_fam  = Prestation(pf._rst_fam, 'fam', label = u"Retraites au sens strict de la famille")
    
    af_nbenf = Prestation(pf._af_nbenf, 'fam', u"Nombre d'enfant au sens des AF")
    af_base  = Prestation(pf._af_base, 'fam', label ='Allocations familiales - Base')
    af_majo  = Prestation(pf._af_majo, 'fam', label ='Allocations familiales - Majoration pour age')
    af_forf  = Prestation(pf._af_forf, 'fam', label ='Allocations familiales - Forfait 20 ans')
    af       = Prestation(pf._af, 'fam', label = u"Allocations familiales")
    
    
    rev_pf   = Prestation(pf._rev_pf, 'fam', label ='Base ressource individuele des prestations familiales')
    br_pf    = Prestation(pf._br_pf, 'fam', label ='Base ressource des prestations familiales')
    cf_temp  = Prestation(pf._cf, 'fam', label = u"Complément familial avant d'éventuels cumuls")
    asf      = Prestation(pf._asf, 'fam', label = u"Allocation de soutien familial")
# TODO mensualisation âge    ars     = Prestation(ARS, 'fam', label = u"Allocation de rentrée scolaire")
    paje_base_temp = Prestation(pf._paje_base, 'fam', label = u"Allocation de base de la PAJE sans tenir compte d'éventuels cumuls")
    paje_base      = Prestation(pf._paje_cumul_cf, 'fam', label = u"Allocation de base de la PAJE")
    cf             = Prestation(pf._cf_cumul_paje, 'fam', label = u"Complément familial avant d'éventuels cumuls")
    paje_nais      = Prestation(pf._paje_nais, 'fam', label = u"Allocation de naissance de la PAJE")
    paje_clca      = Prestation(pf._paje_clca, 'fam', label = u"PAJE - Complément de libre choix d'activité")
    paje_clca_taux_plein      = Prestation(pf._paje_clca_taux_plein, 'fam', label = u"Indicatrice Clca taux plein")
    paje_clca_taux_partiel      = Prestation(pf._paje_clca_taux_partiel, 'fam', label = u"Indicatrice Clca taux partiel ")
    #paje_clmg        = Prestation(Paje_Clmg, 'fam', label = u"PAJE - Complément de libre choix du mode de garde")
    aeeh           = Prestation(pf._aeeh, 'fam', label = u"Allocation d'éducation de l'enfant handicapé")


    asf_elig = Prestation(ir._asf_elig, 'foy')