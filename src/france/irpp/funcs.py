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

from __future__ import division
from numpy import ( maximum as max_, minimum as min_, logical_xor as xor_, 
                    logical_not as not_, round)
from Utils import BarmMar

from france.data import QUIFOY, year

VOUS = QUIFOY['vous']
CONJ = QUIFOY['conj']
PAC1 = QUIFOY['pac1']
PAC2 = QUIFOY['pac2']
PAC3 = QUIFOY['pac3']
ALL = []
for qui in QUIFOY:
    ALL.append(qui[1])
        

# zglof = Glo(table)
# zetrf = zeros(taille)
# jveuf = zeros(taille, dtype = bool)
# jourXYZ = 360*ones(taille)
# Reprise du crédit d'impôt en faveur des jeunes, des accomptes et des versements mensues de prime pour l'emploi
# reprise = zeros(taille) # TODO : reprise=J80
# Pcredit = P.credits_impots
# if hasattr(P.reductions_impots,'saldom'): Pcredit.saldom =  P.reductions_impots.saldom
# credits_impot = Credits(Pcredit, table)
# Réduction d'impôt
# reductions = Reductions(IPnet, P.reductions_impots)

#def mcirra():
#    # impôt sur le revenu
#    mcirra = -((IMP<=-8)*IMP)
#    mciria = max_(0,(IMP>=0)*IMP)
##        mciria = max_(0,(IMP>=0)*IMP - credimp_etranger - cont_rev_loc - ( f8to + f8tb + f8tc ))
#    
#    # Dans l'ERFS, les prelevement libératoire sur les montants non déclarés
#    # sont intégrés. Pas possible de le recalculer.
#    
#    # impot sur le revenu du foyer (hors prélèvement libératoire, revenus au quotient)
#    irpp   = -(mciria + ppetot - mcirra )
    

###############################################################################
## Initialisation de quelques variables utiles pour la suite
###############################################################################

def _nb_adult(marpac, celdiv, veuf):
    return 2*marpac + 1*(celdiv | veuf)

def _nb_pac(nbF, nbJ, nbR):
    return nbF + nbJ + nbR
        
def _marpac(statmarit):
    '''
    Marié ou Pacsé
    'foy'
    '''
    return (statmarit == 1) | (statmarit == 5)

def _celdiv(statmarit):
    '''
    Célibataire ou divorcé
    'foy'
    '''
    return (statmarit == 2) | (statmarit == 3)

def _veuf(statmarit):
    '''
    Veuf
    'foy'
    '''
    return statmarit == 4

def _jveuf(statmarit):
    '''
    Jeune Veuf
    'foy'
    '''
    return statmarit == 6

###############################################################################
## Revenus catégoriels
###############################################################################

def _alloc(af, _P):
    '''
    ALLOCATION FAMILLIALE IMPOSABLE
    '''
    P = _P.ir.autre
    return af*P.alloc_imp

def _rev_sal(sal):
    '''
    Revenu imposé comme des salaires (salaires, mais aussi 3vj, 3vk)
    '''
    return sal

def _sal_net(rev_sal, choCheckBox, fra, _P):
    '''
    Salaires après abattements
    '''
    P = _P.ir.tspr.abatpro
    amin = P.min*not_(choCheckBox) + P.min2*choCheckBox
    abatfor = round(min_(max_(P.taux*rev_sal, amin),P.max))
    return (fra > abatfor)*(rev_sal - fra) \
         + (fra <= abatfor)*max_(0,rev_sal - abatfor)

def _rev_pen(alr, rst):
    '''
    Revenu imposé comme des pensions (retraites, pensions alimentaires, etc.)
    '''
    return alr + rst

def _pen_net(rev_pen, _P):
    '''
    Pensions après abattements
    '''
    P = _P.ir.tspr.abatpen
#    #problème car les pensions sont majorées au niveau du foyer
#    d11 = ( AS + BS + CS + DS + ES + 
#            AO + BO + CO + DO + EO ) 
#    penv2 = (d11-f11> P.abatpen.max)*(penv + (d11-f11-P.abatpen.max)) + (d11-f11<= P.abatpen.max)*penv   
#    # Plus d'abatement de 20% en 2006

    return max_(0, rev_pen - round(max_(P.taux*rev_pen , P.min)))

def _rto_net(f1aw, f1bw, f1cw, f1dw, _P):
    '''
    Rentes viagères après abatements
    '''
    P = _P.ir.tspr.abatviag
    return round(P.taux1*f1aw + 
                 P.taux2*f1bw + 
                 P.taux3*f1cw + 
                 P.taux4*f1dw )

def _tspr(sal_net, pen_net):
    '''
    Traitemens salaires pensions et rentes individuelles
    '''
    return sal_net + pen_net

def _rev_cat_tspr(tspr, rto_net, _option = {'tspr': ALL}):
    '''
    TRAITEMENTS SALAIRES PENSIONS ET RENTES
    '''
    out = 0
    for qui in tspr.itervalues():
        out += qui

    out += rto_net
    
    return out

def _rev_cat_rvcm(marpac, deficit_rcm, f2ch, f2dc, f2ts, f2ca, f2fu, f2go, f2tr, _P):
    '''
    REVENUS DES VALEURS ET CAPITAUX MOBILIERS
    '''
    P = _P.ir.rvcm
    if year > 2004: f2gr = 0

    ## Calcul du revenu catégoriel
    #1.2 Revenus des valeurs et capitaux mobiliers
    b12 = min_(f2ch, P.abat_assvie*(1 + marpac))
    TOT1 = f2ch-b12
    # Part des frais s'imputant sur les revenus déclarés case DC
    den = ((f2dc + f2ts)!=0)*(f2dc + f2ts) + ((f2dc + f2ts)==0)
    F1 =  f2ca/den*f2dc
    
    # Revenus de capitaux mobiliers nets de frais, ouvrant droit à abattement
    # partie négative (à déduire des autres revenus nets de frais d'abattements
    g12a = - min_(f2dc*P.abatmob_taux - F1,0)
    # partie positive
    g12b = max_(f2dc*P.abatmob_taux - F1,0)
    
    rev = g12b + f2gr + f2fu*P.abatmob_taux

    # Abattements, limité au revenu
    h12 = P.abatmob*(1 + marpac)
    TOT2 = max_(0,rev - h12)
    i121= -min_(0,rev - h12)
    
    # Pars des frais s'imputant sur les revenus déclarés ligne TS
    F2 = f2ca - F1
    TOT3 = (f2ts - F2) + f2go*P.majGO + f2tr - g12a

    DEF = deficit_rcm

    ## TODO: pour le calcul du revenu fiscal de référence
    rfr_rvcm = max_((1-P.abatmob_taux)*(f2dc + f2fu) - i121, 0)

    return max_(TOT1 + TOT2 + TOT3 - DEF, 0)

def _rev_cat_rfon(f4ba, f4bb, f4bc, f4bd, f4be, _P):
    '''
    REVENUS FONCIERS
    '''    
    P = _P.ir.microfoncier
    ## Calcul du revenu catégoriel
    a13 = f4ba + f4be - P.taux*f4be*(f4be <= P.max)
    b13 = f4bb
    c13 = a13-b13
    d13 = f4bc
    e13 = c13- d13*(c13>=0)
    f13 = f4bd*(e13>=0)
    g13 = max_(0, e13- f13)
    out  = (c13>=0)*(g13 + e13*(e13<0)) - (c13<0)*d13
    return out

def _rev_cat_rpns(sal):
    return 0*sal

def _rev_cat(rev_cat_tspr, rev_cat_rvcm, rev_cat_rfon, rev_cat_rpns):
    '''
    Revenus Categoriels
    '''
#    AUTRE = TSPR + RVCM + RFON
    return rev_cat_tspr + rev_cat_rvcm + rev_cat_rfon + rev_cat_rpns

###############################################################################
## Déroulé du calcul de l'irpp
###############################################################################

def _rbg(alloc, rev_cat, deficit_ante, f6gh, _P):
    '''
    Revenu brut global (Total 17)
    '''
    # sans les revenus au quotient
    return max_(0, alloc + rev_cat + f6gh - deficit_ante)

def _csg_deduc(rbg, f6de):
    '''
    CSG déductible
    '''
    return min_(f6de, max_(rbg, 0))

def _rng(rbg, csg_deduc, charges_deduc):
    '''
    Revenu net global (total 20)
    '''
    return max_(0, rbg - csg_deduc - charges_deduc)

def _rni(rng, abat_spe):
    return rng - abat_spe

def _ir_brut(nbptr, rni, _P):
    '''
    Impot sur le revenu avant non imposabilité et plafonnement du quotien
    'foy'
    '''
    P = _P.ir.bareme
    return nbptr*BarmMar(rni/nbptr, P) # TODO : partir d'ici, petite différence avec Matlab

def _ir_plaf_qf(ir_brut, rni, nb_adult, nb_pac, nbptr, marpac, veuf, jveuf, celdiv, caseE, caseF, caseG, caseH, caseK, caseN, caseP, caseS, caseT, caseW, nbF, nbG, nbH, nbI, nbR, _P):
    '''
    Impôt après plafonnement du quotient familial et réduction complémentaire
    '''
    P = _P.ir
    I = ir_brut
    A = BarmMar(rni/nb_adult,P.bareme)
    A = nb_adult*A    

    aa0 = (nbptr-nb_adult)*2           #nombre de demi part excédant nbadult
    # on dirait que les impôts font une erreur sur aa1 (je suis obligé de
    # diviser par 2)
    aa1 = min_((nbptr-1)*2,2)/2  # deux première demi part excédants une part
    aa2 = max_((nbptr-2)*2,0)    # nombre de demi part restantes
    # celdiv parents isolés
    condition61 = (celdiv==1) & caseT
    B1 = P.plafond_qf.celib_enf*aa1 + P.plafond_qf.marpac*aa2
    # tous les autres
    B2 = P.plafond_qf.marpac*aa0                 #si autre
    # celdiv, veufs (non jveuf) vivants seuls et autres conditions TODO année codéee en dur
    # TODO: année en dur... pour caseH
    condition63 = ((celdiv==1) | ((veuf==1) & not_(jveuf))) & not_(caseN) & (nb_pac==0) & (caseK | caseE) & (caseH<1981)
    B3 = P.plafond_qf.celib

    B = B1*condition61 + \
        B2*(not_(condition61 | condition63)) + \
        B3*(condition63 & not_(condition61))
    C = max_(0,A-B)
    # Impôt après plafonnement
    IP0 = max_(I, C) #I*(I>=C) + C*(I<C)

    # 6.2 réduction d'impôt pratiquée sur l'impot après plafonnement et le cas particulier des DOM
    # pas de réduction complémentaire
    condition62a = (I>=C)
    # réduction complémentaire
    condition62b = (I<C)
    # celdiv veuf
    condition62caa0 = (celdiv | (veuf & not_(jveuf)))
    condition62caa1 = (nb_pac==0)&(caseP | caseG | caseF | caseW)
    condition62caa2 = caseP & ((nbF-nbG>0)|(nbH - nbI>0))
    condition62caa3 = not_(caseN) & (caseE | caseK )  & (caseH>=1981)
    condition62caa  = condition62caa0 & (condition62caa1 | condition62caa2 | condition62caa3)
    # marié pacs
    condition62cab = (marpac | jveuf) & caseS & not_(caseP | caseF)
    condition62ca =    (condition62caa | condition62cab)

    # plus de 590 euros si on a des plus de
    condition62cb = ((nbG+nbR+nbI)>0) | caseP | caseF
    D = P.plafond_qf.reduc_postplafond*(condition62ca + ~condition62ca*condition62cb*( 1*caseP + 1*caseF + nbG + nbR + nbI/2 ))

    E = max_(0,A-I-B)
    Fo = D*(D<=E) + E*(E<D)
    out = IP0-Fo

    return out
    # TODO :6.3 Cas particulier: Contribuables domiciliés dans les DOM.    
    # conditionGuadMarReu =
    # conditionGuyane=
    # conitionDOM = conditionGuadMarReu | conditionGuyane
    # postplafGuadMarReu = 5100
    # postplafGuyane = 6700
    # IP2 = IP1 - conditionGuadMarReu*min( postplafGuadMarReu,.3*IP1)  - conditionGuyane*min(postplafGuyane,.4*IP1)
#
#
#    # Récapitulatif
#    return condition62a*IP0 + condition62b*IP1 # IP2 si DOM

def _decote(ir_plaf_qf, _P):
    '''
    Décote
    '''
    P = _P.ir.decote
    return (ir_plaf_qf < P.seuil)*(P.seuil - ir_plaf_qf)*0.5

def _nat_imp(rni, nbptr, _P):
    '''
    Renvoie 1 si le foyer est imposable, 0 sinon
    '''
    P = _P.ir.non_imposable
    seuil = P.seuil + (nbptr - 1)*P.supp
    return rni >= seuil

def _ip_net(ir_plaf_qf, nat_imp, decote):
    '''
    irpp après décote et prise en compte de la non imposabilité
    '''
    return nat_imp*max_(0, ir_plaf_qf - decote)

def _iaidrdi(ip_net, reductions):
    '''
    impot après imputation des réductions d'impôt
    '''
    return   ip_net - reductions

def _cont_rev_loc(f4bl):
    '''
    Contribution sur les revenus locatifs
    '''
    loyf_taux = 0.025
    loyf_seuil = 0
    return round(loyf_taux *(f4bl >= loyf_seuil)*f4bl)

def _teicaa(f5qm, f5rm):
    '''
    Taxe exceptionelle sur l'indemnité compensatrice des agents d'assurance
    '''
    #     H90_a1 = 0*max_(0,min_(f5qm,23000))
    H90_a2 = .04*max_(0,min_(f5qm - 23000,107000))
    H90_a3 = .026*max_(0,f5qm - 107000)
    #     H90_b1 = 0*max_(0,min_(f5rm,23000))
    H90_b2 = .04*max_(0,min_(f5qm-23000,107000))
    H90_b3 = .026*max_(0,f5qm - 107000)
    
    return H90_a2 + H90_a3 + H90_b2 + H90_b3

def _iai(iaidrdi, plus_values, cont_rev_loc, teicaa):
    '''
    impôt avant imputation
    '''
    return iaidrdi + plus_values + cont_rev_loc + teicaa

def _tehr(rfr, nb_adult, P):
    '''
    Taxe exceptionnelle sur les hauts revenus
    'foy'
    '''
    return BarmMar(rfr/nb_adult, P)*nb_adult
    
def _irpp(iai, credits_impot, tehr, ppe):
    '''
    Montant avant seuil de recouvrement (hors ppe)
    '''
    return  iai - credits_impot + ppe + tehr


###############################################################################
## Autres totaux utiles pour la suite
###############################################################################

def _rfr(rni, alloc, f3va, f3vg, f3vi, rfr_cd, rfr_rvcm, rpns_exo, rpns_pvce, rev_cap_lib):
    '''
    Revenu fiscal de reference
    '''
    return max_(0, rni - alloc) + rfr_cd + rfr_rvcm + rev_cap_lib + f3vi + rpns_exo + rpns_pvce + f3va + f3vg
 
def _glo(f1tv, f1tw, f1tx, f1uv, f1uw, f1ux, f3vf, f3vi, f3vj, f3vk):
    '''
    Gains de levée d'option
    'foy'
    '''
    return f1tv + f1tw + f1tx + f1uv + f1uw + f1ux + f3vf + f3vi + f3vj + f3vk                   

def _rto(f1aw, f1bw, f1cw, f1dw):
    '''
    Rentes viagères à titre onéreux
    '''
    return f1aw + f1bw + f1cw + f1dw

def _deficit_rcm(f2aa, f2al, f2am, f2an):
    return f2aa + f2al + f2am + f2an
    
def _rev_cap_bar(f2dc, f2gr, f2ch, f2ts, f2go, f2tr, f2fu, avf):
    '''
    revenus du capital imposés au barème
    '''
    return f2dc + f2gr + f2ch + f2ts + f2go + f2tr + f2fu - avf

def _rev_cap_lib(f2da, f2dh, f2ee):
    '''
    Revenu du capital imposé au prélèvement libératoire
    '''
    if year <=2007: out = f2dh + f2ee
    else: out = f2da + f2dh + f2ee
    return out

def _avf(f2ab):
    # a.(ii) Avoir fiscal et crédits d'impôt (zavff)
    return f2ab
    # a.(iii) Les revenus de valeurs mobilières soumis au prélèvement
    # libératoire (zvalf)

    
def _imp_lib(f2da, f2dh, f2ee, _P):
    '''
    Prelèvement libératoire sur les revenus du capital
    '''
    P = _P.ir.prelevement_liberatoire
    if year <=2007: 
        out = - (P.assvie*f2dh + P.autre*f2ee )
    else:
        out = - (P.action*f2da + P.assvie*f2dh + P.autre*f2ee )
    return out

def _rfon_rmi(f4ba, f4be):
    '''
    Revenus fonciers pour la base ressource du rmi/rsa
    '''
    return f4ba + f4be


def _fon(f4ba, f4bb, f4bc, f4bd, f4be, _P):
    ## Calcul des totaux        
    P = _P.ir.microfoncier
    fon = f4ba - f4bb - f4bc + round(f4be*(1-P.taux))  
    return fon

def _rpns_pvce(frag_pvce, arag_pvce, nrag_pvce, mbic_pvce, abic_pvce, 
               nbic_pvce, macc_pvce, aacc_pvce, nacc_pvce, mbnc_pvce, 
               abnc_pvce, nbnc_pvce, mncn_pvce, cncn_pvce):
    ''' 
    Plus values de cession
    'ind'
    frag_pvce (f5hx, f5ix, f5jx)
    arag_pvce (f5he, f5ie, f5je)
    nrag_pvce (f5hk, f5ik, f5jk)
    mbic_pvce (f5kq, f5lq, f5mq)
    abic_pvce (f5ke, f5le, f5me)
    nbic_pvce (f5kk, f5lk, f5mk)
    macc_pvce (f5nq, f5oq, f5pq)
    aacc_pvce (f5ne, f5oe, f5pe)
    nacc_pvce (f5nk, f5ok, f5pk)
    mncn_pvce (f5kv, f5lv, f5mv)
    cncn_pvce (f5so, f5nt, f5ot)
    mbnc_pvce (f5hr, f5ir, f5jr)
    abnc_pvce (f5qd, f5rd, f5sd)
    nbnc_pvce (f5qj, f5rj, f5sj)
    '''

    return ( frag_pvce + arag_pvce + nrag_pvce + mbic_pvce + abic_pvce + 
             nbic_pvce + macc_pvce + aacc_pvce + nacc_pvce + mbnc_pvce + 
             abnc_pvce + nbnc_pvce + mncn_pvce + cncn_pvce )

def _rpns_exon(frag_exon, arag_exon, nrag_exon, mbic_exon, abic_exon, 
               nbic_exon, macc_exon, aacc_exon, nacc_exon, mbnc_exon, 
               abnc_exon, nbnc_exon ):
    ''' 
    Plus values de cession
    'ind'
    frag_exon (f5hn, f5in, f5jn)
    arag_exon (f5hb, f5ib, f5jb)
    nrag_exon (f5hh, f5ih, f5jh)
    mbic_exon (f5kn, f5ln, f5mn)
    abic_exon (f5kb, f5lb, f5mb)
    nbic_exon (f5kh, f5lh, f5mh)
    macc_exon (f5nn, f5on, f5pn)
    aacc_exon (f5nb, f5ob, f5pb)
    nacc_exon (f5nh, f5oh, f5ph)
    mbnc_exon (f5hp, f5ip, f5jp)
    abnc_exon (f5qb, f5rb, f5sb)
    nbnc_exon (f5qh, f5rh, f5sh)
    '''
    
    return (frag_exon + arag_exon + nrag_exon + mbic_exon + abic_exon + 
            nbic_exon + macc_exon + aacc_exon + nacc_exon + mbnc_exon + 
            abnc_exon + nbnc_exon )
    
def _rag(frag_exon, frag_impo, arag_exon, arag_impg, arag_defi, nrag_exon, nrag_impg, nrag_defi, nrag_ajag):
    '''
    Revenus agricoles
    'ind'
    frag_exon (f5hn, f5in, f5jn)
    frag_impo (f5ho, f5io, f5jo)    
    arag_exon (f5hb, f5ib, f5jb)
    arag_impg (f5hc, f5ic, f5jc)
    arag_defi (f5hf, f5if, f5jf)
    nrag_exon (f5hh, f5ih, f5jh)
    nrag_impg (f5hi, f5ii, f5ji)
    nrag_defi (f5hl, f5il, f5jl)
    nrag_ajag (f5hm, f5im, f5jm)
    '''    
    return (frag_exon + frag_impo + 
            arag_exon + arag_impg - arag_defi + 
            nrag_exon + nrag_impg - nrag_defi + 
            nrag_ajag)

def _ric(mbic_exon, mbic_impv, mbic_imps, abic_exon, nbic_exon, abic_impn, nbic_impn,
         abic_imps, nbic_imps, abic_defn, nbic_defn, abic_defs, nbic_defs, nbic_apch, _P):
    '''
    Bénéfices industriels et commerciaux
    'ind'
    mbic_exon (f5kn, f5ln, f5mn)
    abic_exon (f5kb, f5lb, f5mb)
    nbic_exon (f5kh, f5lh, f5mh)
    mbic_impv (f5ko, f5lo, f5mo)
    mbic_imps (f5kp, f5lp, f5mp)
    abic_impn (f5kc, f5lc, f5mc)
    abic_imps (f5kd, f5ld, f5md)
    nbic_impn (f5ki, f5li, f5mi)
    nbic_imps (f5kj, f5lj, f5mj)
    abic_defn (f5kf, f5lf, f5mf)
    abic_defs (f5kg, f5lg, f5mg)
    nbic_defn (f5kl, f5ll, f5ml)
    nbic_defs (f5km, f5lm, f5mm)
    nbic_apch (f5ks, f5ls, f5ms)
    '''
    
    P = _P.ir.rpns.microentreprise
        
    zbic =(  mbic_exon + mbic_impv + mbic_imps
           + abic_exon + nbic_exon 
           + abic_impn + nbic_impn 
           + abic_imps + nbic_imps 
           - abic_defn - nbic_defn 
           - abic_defs - nbic_defs 
           + nbic_apch)
    
    cond = (mbic_impv>0) & (mbic_imps==0)
    taux = P.vente_taux*cond + P.servi_taux*not_(cond)
    
    P.cbicf_min = 305
    
    cbic = min_(mbic_impv + mbic_imps + mbic_exon, 
                max_(P.cbicf_min,round(mbic_impv*P.vente_taux + mbic_imps*P.servi_taux + mbic_exon*taux)))
    
    ric = zbic - cbic

    return ric

def _rac(macc_exon, macc_impv, macc_imps,
         aacc_exon, aacc_impn, aacc_imps, aacc_defn, aacc_defs,
         nacc_exon, nacc_impn, nacc_imps, nacc_defn, nacc_defs,
         mncnp_impo, cncnp_bene, cncnp_defi, _P):
    '''
    Revenus accessoires individuels
    'ind'
    macc_exon (f5nn, f5on, f5pn)
    aacc_exon (f5nb, f5ob, f5pb)
    nacc_exon (f5nh, f5oh, f5ph)
    macc_impv (f5no, f5oo, f5po)
    macc_imps (f5np, f5op, f5pp)
    aacc_impn (f5nc, f5oc, f5pc)
    aacc_imps (f5nd, f5od, f5pd)
    aacc_defn (f5nf, f5of, f5pf)
    aacc_defs (f5ng, f5og, f5pg)
    nacc_impn (f5ni, f5oi, f5pi)
    nacc_imps (f5nj, f5oj, f5pj)
    nacc_defn (f5nl, f5ol, f5pl)
    nacc_defs (f5nm, f5om, f5pm)
    mncnp_impo (f5ku, f5lu, f5mu)
    cncnp_bene (f5sn, f5ns, f5os)
    cncnp_defi (f5sp, f5nu, f5ou, f5sr)
    f5sv????
    '''
    P = _P.ir.rpns.microentreprise

    zacc = (  macc_exon + macc_impv + macc_imps 
            + aacc_exon + aacc_impn + aacc_imps - aacc_defn - aacc_defs 
            + nacc_exon + nacc_impn + nacc_imps - nacc_defn - nacc_defs 
            + mncnp_impo + cncnp_bene - cncnp_defi)
    
    cond = (macc_impv >0) & (macc_imps ==0)
    taux = P.vente_taux*cond + P.servi_taux*not_(cond)
    
    cacc = min_(macc_impv + macc_imps + macc_exon + mncnp_impo, 
                max_(P.nc_abat_min,
                     round(macc_impv*P.vente_taux + macc_imps*P.servi_taux + macc_exon*taux + mncnp_impo*P.nc_abat_taux )))
    
    rac = zacc - cacc
    
    return rac

def _rnc(mbnc_exon, mbnc_impo, abnc_exon, nbnc_exon, abnc_impo, nbnc_impo, abnc_defi, nbnc_defi, _P):
    '''
    Revenus non commerciaux individuels
    'ind'
    mbnc_exon (f5hp, f5ip, f5jp)
    abnc_exon (f5qb, f5rb, f5sb)
    nbnc_exon (f5qh, f5rh, f5sh)
    mbnc_impo (f5hq, f5iq, f5jq)
    abnc_impo (f5qc, f5rc, f5sc)
    abnc_defi (f5qe, f5re, f5se)
    nbnc_impo (f5qi, f5ri, f5si)
    nbnc_defi (f5qk, f5rk, f5sk)
    f5ql, f5qm????
    '''
    P = _P.ir.rpns.microentreprise

    zbnc = (  mbnc_exon + mbnc_impo 
            + abnc_exon + nbnc_exon 
            + abnc_impo + nbnc_impo 
            - abnc_defi - nbnc_defi )
        
    cbnc = min_(mbnc_exon + mbnc_impo, max_(P.nc_abat_min, round((mbnc_exon + mbnc_impo)*P.nc_abat_taux)))
    
    rnc = zbnc - cbnc
    return rnc


def _rpns(rag, ric, rac, rnc):
    '''
    Revenus des professions non salariées individuels
    'ind'
    '''
    return rag + ric + rac + rnc

def _rpns_pvct(frag_pvct, mbic_pvct, macc_pvct, mbnc_pvct, mncn_pvct):
    '''
    Plus values de court terme
    'ind'
    frag_pvct (f5hw, f5iw, f5jw)
    mbic_pvct (f5kx, f5lx, f5mx)
    macc_pvct (f5nx, f5ox, f5px)
    mbnc_pvct (f5hv, f5iv, f5jv)
    mncn_pvct (f5ky, f5ly, f5my)
    '''
    return frag_pvct + mbic_pvct + macc_pvct + mbnc_pvct + mncn_pvct

def _rpns_mvct(mbic_mvct, macc_mvct, mbnc_mvct, mncn_mvct):
    '''
    Moins values de court terme
    'ind'
    mbic_mvct (f5hu)
    macc_mvct (f5iu)
    mncn_mvct (f5ju)
    mbnc_mvct (f5kz)

    '''
    return mbic_mvct + macc_mvct + mbnc_mvct + mncn_mvct

def _rpns_mvlt(mbic_mvlt, macc_mvlt, mbnc_mvlt, mncn_mvlt):
    '''
    Moins values de long terme
    'ind'
    mbic_mvlt (f5kr, f5lr, f5mr)
    macc_mvlt (f5nr, f5or, f5pr)
    mncn_mvlt (f5kw, f5lw, f5mw)
    mbnc_mvlt (f5hs, f5is, f5js)
    '''
    return mbic_mvlt + macc_mvlt + mbnc_mvlt + mncn_mvlt
    
#def _rpns_full(self, P, table):
#    '''
#    REVENUS DES PROFESSIONS NON SALARIEES
#    partie 5 de la déclaration complémentaire
#    '''
#
#    def abatv(rev, P):
#        return max_(0,rev - min_(rev, max_(P.microentreprise.vente_taux*min_(P.microentreprise.vente_max, rev), P.microentreprise.vente_min)))
#    
#    def abats(rev, P):
#        return max_(0,rev - min_(rev, max_(P.microentreprise.servi_taux*min_(P.microentreprise.servi_max, rev), P.microentreprise.servi_min)))
#    
#    def abatnc(rev, P):
#        return max_(0,rev - min_(rev, max_(P.nc_abat_taux*min_(P.nc_abat_max, rev), P.nc_abat_min)))
#
#
#    #regime du forfait
#    frag_impo = f5ho + f5io + f5jo
#    frag_pvct = f5hw + f5iw + f5jw
#    frag_timp = frag_impo + frag_pvct  # majoration de 25% mais les pvct ne sont pas majorées de 25%
#    
#    #Régime du bénéfice réel ou transitoire bénéficiant de l'abattement CGA
#    arag_impg = f5hc + f5ic + f5jc
#    arag_defi = f5hf + f5if + f5jf
#    arag_timp = arag_impg                  # + aragf_impx/5 pas de majoration
#    
#    #Régime du bénéfice réel ou transitoire ne bénéficiant pas de l'abattement CGA
#    nrag_impg = f5hi + f5ii + f5ji
#    nrag_defi = f5hl + f5il + f5jl
#    nrag_timp = nrag_impg # + nragf_impx/5  # majoration de 25% mais les pvct ne sont pas majorées de 25%
#    
#    #Jeunes agriculteurs montant de l'abattement de 50% ou 100% 
#    nrag_ajag = f5hm + f5im + f5jm 
#    # TODO: à integrer qqpart
#    
#    # déficits agricole des années antérieurs (imputables uniquement
#    # sur des revenus agricoles)
#    rag_timp = frag_timp + arag_timp + nrag_timp 
#    cond = (AUTRE <= P.def_agri_seuil)
#    def_agri = cond*(arag_defi + nrag_defi) + not_(cond)*min_(rag_timp, arag_defi + nrag_defi)
#    # TODO : check 2006 cf art 156 du CGI pour 2006
#    # sur base 2003:
#    # cf menage 3020938 pour le déficit agricole qui peut déduire et ménage
#    # 3001872 qui ne peut pas déduire.
#    def_agri_ant    = min_(max_(0,rag_timp - def_agri), f5sq)
#
#    ## B revenus industriels et commerciaux professionnels     
#    #regime micro entreprise
#    mbic_impv = abatv(f5ko,P) + abatv(f5lo,P) + abatv(f5mo,P)
#    mbic_imps = abats(f5kp,P) + abats(f5lp,P) + abats(f5mp,P)
#    mbic_pvct = f5kx + f5lx + f5mx
#    mbic_mvlt = f5kr + f5lr + f5mr
#    mbic_mvct = f5hu
#    mbic_timp = mbic_impv + mbic_imps - mbic_mvlt
#    
#    #Régime du bénéfice réel bénéficiant de l'abattement CGA
#    abic_impn = f5kc + f5lc + f5mc
#    abic_imps = f5kd + f5ld + f5md
#    abic_defn = f5kf + f5lf + f5mf
#    abic_defs = f5kg + f5lg + f5mg
#    abic_timp = abic_impn + abic_imps - (abic_defn + abic_defs)
#    abic_defe = -min_(abic_timp,0) 
#    # base 2003: cf ménage 3021218 pour l'imputation illimitée de ces déficits.
#    
#    #Régime du bénéfice réel ne bénéficiant pas de l'abattement CGA
#    nbic_impn = f5ki + f5li + f5mi
#    nbic_imps = f5kj + f5lj + f5mj
#    nbic_defn = f5kl + f5ll + f5ml
#    nbic_defs = f5km + f5lm + f5mm
#    nbic_timp = (nbic_impn + nbic_imps) - (nbic_defn + nbic_defs)
#    nbic_defe = -min_(nbic_timp,0) 
#    # base 2003 cf ménage 3015286 pour l'imputation illimitée de ces déficits.
#    
#    #Abatemment artisant pécheur
#    nbic_apch = f5ks + f5ls + f5ms # TODO : à intégrer qqpart
#        
#    
#    ## C revenus industriels et commerciaux non professionnels 
#    # (revenus accesoires du foyers en nomenclature INSEE)
#    #regime micro entreprise
#    macc_impv = abatv(f5no,P) + abatv(f5oo,P) + abatv(f5po,P)
#    macc_imps = abats(f5np,P) + abats(f5op,P) + abats(f5pp,P)
#    macc_pvct = f5nx + f5ox + f5px
#    macc_mvlt = f5nr + f5or + f5pr
#    macc_mvct = f5iu
#    macc_timp = macc_impv + macc_imps - macc_mvlt
#    
#    #Régime du bénéfice réel bénéficiant de l'abattement CGA
#    aacc_impn = f5nc + f5oc + f5pc
#    aacc_imps = f5nd + f5od + f5pd
#    aacc_defn = f5nf + f5of + f5pf
#    aacc_defs = f5ng + f5og + f5pg
#    aacc_timp = max_(0,aacc_impn + aacc_imps - (aacc_defn + aacc_defs))
#    
#    #Régime du bénéfice réel ne bénéficiant pas de l'abattement CGA
#    nacc_impn = f5ni + f5oi + f5pi
#    nacc_imps = f5nj + f5oj + f5pj
#    nacc_defn = f5nl + f5ol + f5pl
#    nacc_defs = f5nm + f5om + f5pm
#    nacc_timp = max_(0,nacc_impn + nacc_imps - (nacc_defn + nacc_defs))
#    # TODO : base 2003 comprendre pourquoi le ménage 3018590 n'est pas imposé sur 5nj.
#    
#    ## E revenus non commerciaux non professionnels 
#    #regime déclaratif special ou micro-bnc
#    mncn_impo = abatnc(f5ku,P) + abatnc(f5lu,P) + abatnc(f5mu,P)
#    mncn_pvct = f5ky + f5ly + f5my
#    mncn_mvlt = f5kw + f5lw + f5mw
#    mncn_mvct = f5ju
#    mncn_timp = mncn_impo - mncn_mvlt
#    
#    # TODO : 2006 
#    # régime de la déclaration controlée 
#    cncn_bene = f5sn + f5ns + f5os
#    cncn_defi = f5sp + f5nu + f5ou + f5sr
#    #total 11
#    cncn_timp = max_(0,cncn_bene - cncn_defi) 
#    # TODO : abatement jeunes créateurs 
#    
#    ## D revenus non commerciaux professionnels
#    #regime déclaratif special ou micro-bnc
#    mbnc_impo = abatnc(f5hq,P) + abatnc(f5iq,P) + abatnc(f5jq,P)
#    mbnc_pvct = f5hv + f5iv + f5jv
#    mbnc_mvlt = f5hs + f5is + f5js
#    mbnc_mvct = f5kz
#    mbnc_timp = mbnc_impo - mbnc_mvlt
#    
#    #regime de la déclaration contrôlée bénéficiant de l'abattement association agréée
#    abnc_impo = f5qc + f5rc + f5sc
#    abnc_defi = f5qe + f5re + f5se
#    abnc_timp = abnc_impo - abnc_defi
#    
#    #regime de la déclaration contrôlée ne bénéficiant pas de l'abattement association agréée
#    nbnc_impo = f5qi + f5ri + f5si 
#    nbnc_defi = f5qk + f5rk + f5sk 
#    nbnc_timp = nbnc_impo - nbnc_defi
#    # cf base 2003 menage 3021505 pour les deficits
#    
#    ## Totaux
#    atimp = arag_timp + abic_timp +  aacc_timp + abnc_timp
#    ntimp = nrag_timp + nbic_timp +  nacc_timp + nbnc_timp
#    
#    majo_cga = max_(0,P.cga_taux2*(ntimp + frag_impo)) # pour ne pas avoir à
#                                            # majorer les déficits
#    #total 6
#    rev_NS = frag_impo + frag_pvct + atimp + ntimp + majo_cga - def_agri - def_agri_ant 
#    
#    #revenu net après abatement
#    # total 7
#    rev_NS_mi = mbic_timp + macc_timp + mbnc_timp + mncn_timp 
#        
#    #plus value ou moins value à court terme
#    #activité exercée à titre professionnel 
#    # total 8
#    pvct_pro = mbic_pvct - mbic_mvct + mbnc_pvct - mbnc_mvct
#    #activité exercée à titre non professionnel
#    #revenus industriels et commerciaux non professionnels 
#    # total 9
#    pvct_icnpro = min_(macc_pvct - macc_mvct, macc_timp) 
#    #revenus non commerciaux non professionnels 
#    # total 10
#    pvct_ncnpro = min_(mncn_pvct - mncn_mvct, mncn_timp)
#    
#    RPNS = rev_NS + rev_NS_mi + pvct_pro + pvct_icnpro + pvct_ncnpro + cncn_timp
#    
#    return RPNS

def _deficit_ante(f6fa, f6fb, f6fc, f6fd, f6fe, f6fl):
    '''
    Déficits antérieurs
    '''
    return f6fa + f6fb + f6fc + f6fd + f6fe + f6fl


#def Charges_deductibles(self, P):
#    '''
#    Charges déductibles
#    '''
#    table = population
#
#    table.openReadMode()
#    niches1, niches2, ind_rfr = charges_deductibles.niches(year)
#    charges_deductibles.charges_calc(self, P, table, niches1, niches2, ind_rfr)
#
#    ## stockage des pensions dans les individus
#    zalvf = charges_deductibles.penali(self, P, table)
#    table.close_()
#
#    table.openWriteMode()
#    table.setColl('alv', -zalvf, table = 'output')
#    table.close_()

def _abat_spe(age, caseP, caseF, rng, nbN, _P, _option = {'age': [VOUS, CONJ]}):
    '''
    Abattements spéciaux 
    - pour personnes âges ou invalides : Si vous êtes âgé(e) de plus de 65 ans
      ou invalide (titulaire d’une pension d’invalidité militaire ou d’accident 
      du travail d’au moins 40 % ou titulaire de la carte d’invalidité), vous 
      bénéficiez d’un abattement de 2 172 € si le revenu net global de votre 
      foyer fiscal n’excède pas 13 370 € ; il est de 1 086 € si ce revenu est 
      compris entre 13 370 € et 21 570 €. Cet abattement est doublé si votre 
      conjoint ou votre partenaire de PACS remplit également ces conditions 
      d’âge ou d’invalidité. Cet abattement sera déduit automatiquement lors 
      du calcul de l’impôt.
    - pour enfants à charge ayant fondé un foyer distinct : Si vous avez accepté
      le rattachement de vos enfants mariés ou pacsés ou de vos enfants 
      célibataires, veufs, divorcés, séparés, chargés de famille, vous bénéficiez 
      d’un abattement sur le revenu imposable de 5 495 € par personne ainsi 
      rattachée. Si l’enfant de la personne rattachée est réputé à charge de 
      l’un et l’autre de ses parents (garde alternée), cet abattement est divisé 
      par deux soit 2 748€. Exemple : 10 990 € pour un jeune ménage et 8 243 €
      pour un célibataire avec un jeune enfant en résidence alternée.
    '''
    ageV, ageC = age[VOUS], age[CONJ]
    invV, invC = caseP, caseF
    P = _P.ir.abattements_speciaux
    as_inv = P.inv_montant*((rng <= P.inv_max1) + 
                            ((rng > P.inv_max1)&(rng <= P.inv_max2))*0.5*(1*(((ageV>=65)&(ageV>0))| invV) + 
                                                                        1*(((ageC>=65)&(ageC>0))| invC) )  )
    as_enf = nbN*P.enf_montant 

    return min_(rng, as_inv + as_enf)

def _nbptr(nb_pac, marpac, celdiv, veuf, jveuf, nbF, nbG, nbH, nbI, nbR, nbJ, caseP, caseW, caseG, caseE, caseK, caseN, caseF, caseS, caseL, caseT, _P):
    '''
    nombre de parts du foyer
    note 1 enfants et résidence alternée (formulaire 2041 GV page 10)
    
    P.enf1 : nb part 2 premiers enfants
    P.enf2 : nb part enfants de rang 3 ou plus
    P.inv1 : nb part supp enfants invalides (I, G)
    P.inv2 : nb part supp adultes invalides (R)
    P.not31 : nb part supp note 3 : cases W ou G pour veuf, celib ou div
    P.not32 : nb part supp note 3 : personne seule ayant élevé des enfants
    P.not41 : nb part supp adultes invalides (vous et/ou conjoint) note 4
    P.not42 : nb part supp adultes anciens combattants (vous et/ou conjoint) note 4
    P.not6 : nb part supp note 6
    P.isol : demi-part parent isolé (T)
    P.edcd : enfant issu du mariage avec conjoint décédé;
    '''
    P = _P.ir.quotient_familial
    no_pac  = nb_pac == 0 # Aucune personne à charge en garde exclusive
    has_pac = not_(no_pac)
    no_alt  = nbH == 0 # Aucun enfant à charge en garde alternée
    has_alt = not_(no_alt)
    
    ## nombre de parts liées aux enfants à charge
    # que des enfants en résidence alternée
    enf1 = (no_pac & has_alt)*(P.enf1*min_(nbH,2)*0.5 + P.enf2*max_(nbH-2,0)*0.5)
    # pas que des enfants en résidence alternée
    enf2 = (has_pac & has_alt)*((nb_pac==1)*(P.enf1*min_(nbH,1)*0.5 + P.enf2*max_(nbH-1,0)*0.5) + (nb_pac>1)*(P.enf2*nbH*0.5))
    # pas d'enfant en résidence alternée    
    enf3 = P.enf1*min_(nb_pac,2) + P.enf2*max_((nb_pac-2),0)
    
    enf = enf1 + enf2 + enf3 
    ## note 2 : nombre de parts liées aux invalides (enfant + adulte)
    n2 = P.inv1*(nbG + nbI/2) + P.inv2*nbR 
    
    ## note 3 : Pas de personne à charge
    # - invalide 

    n31a = P.not31a*( no_pac & no_alt & caseP )
    # - ancien combatant 
    n31b = P.not31b*( no_pac & no_alt & ( caseW | caseG ) ) 
    n31 = max_(n31a,n31b)
    # - personne seule ayant élevé des enfants
    n32 = P.not32*( no_pac & no_alt &(( caseE | caseK) & not_(caseN)))
    n3 = max_(n31,n32)
    ## note 4 Invalidité de la personne ou du conjoint pour les mariés ou
    ## jeunes veuf(ve)s
    n4 = max_(P.not41*(1*caseP + 1*caseF), P.not42*(caseW | caseS))
    
    ## note 5
    #  - enfant du conjoint décédé
    n51 =  P.cdcd*(caseL & ((nbF + nbJ)>0))
    #  - enfant autre et parent isolé
    n52 =  P.isol*caseT*( ((no_pac & has_alt)*((nbH==1)*0.5 + (nbH>=2))) + 1*has_pac)
    n5 = max_(n51,n52)
    
    ## note 6 invalide avec personne à charge
    n6 = P.not6*(caseP & (has_pac | has_alt))
    
    ## note 7 Parent isolé
    n7 = P.isol*caseT*((no_pac & has_alt)*((nbH==1)*0.5 + (nbH>=2)) + 1*has_pac)
    
    ## Régime des mariés ou pacsés
    m = 2 + enf + n2 + n4
    
    ## veufs  hors jveuf
    v = 1 + enf + n2 + n3 + n5 + n6
    
    ## celib div
    c = 1 + enf + n2 + n3 + n6 + n7
    return (marpac | jveuf)*m + (veuf & not_(jveuf))*v + celdiv*c
    

#def Reductions(self, IPnet, P, table):
#    ''' 
#    Réductions d'impôts
#    '''
#    table.openReadMode()
#    niches = reductions_impots.niches(year)
#    reducs = zeros(taille)
#    for niche in niches:
#        reducs += niche(self, P, table)
#         
#    table.close_()
#    return min_(reducs, IPnet)

def _plus_values(f3vg, f3vh, f3vl, f3vm, f3vi, f3vf, f3vd, rpns_pvce, _P):
    P = _P.ir.plus_values
        # revenus taxés à un taux proportionnel
    rdp = max_(0,f3vg - f3vh) + f3vl + rpns_pvce + f3vm + f3vi + f3vf
    out = (P.pvce*rpns_pvce +
           P.taux1*max_(0,f3vg - f3vh) +
           P.caprisque*f3vl +
           P.pea*f3vm +
           P.taux3*f3vi +
           P.taux4*f3vf )
    if year >= 2008:
        # revenus taxés à un taux proportionnel
        rdp += f3vd
        out += P.taux1*f3vd
        
    return round(out)

def _div(rpns_pvce, rpns_pvct, rpns_mvct, rpns_mvlt, f3vc, f3ve, f3vg, f3vh, f3vl, f3vm):
    return f3vc + f3ve + f3vg - f3vh + f3vl+ f3vm + rpns_pvce + rpns_pvct - rpns_mvct - rpns_mvlt
    

def _div_rmi(f3vc, f3ve, f3vg, f3vl, f3vm):
    return f3vc + f3ve + f3vg + f3vl+ f3vm
    
def _rev_coll(rto_net, rev_cap_lib, rev_cap_bar, div, abat_spe, glo, fon, f7ga, f7gb, f7gc):
    '''
    revenus collectif
    'foy'
    '''
    # TODO: ajouter les revenus de l'étranger etr*0.9
    # TODO: ajouter les pensions alimentaires versées
    alv = 0
    return rto_net + rev_cap_lib + rev_cap_bar  + fon + glo - alv - f7ga - f7gb - f7gc - abat_spe
    
    # pour le calcul de l'allocation de soutien familial     
def _asf_elig(caseT, caseL):
    return caseT | caseL

def al_nbinv(nbR):
    return nbR

#def Credits(self, P, table):
#    '''
#    Imputations (crédits d'impôts)
#    '''
#    table.openReadMode()
#    niches = credits_impots.niches(year)
#    reducs = zeros(taille)
#    for niche in niches:
#        reducs += niche(self, P, table)
#    table.close_()
#
#    ppe = Ppe(P.ppe)
#
#    return reducs + ppe

###############################################################################
## Calcul de la prime pour l'emploi
###############################################################################

def _ppe_coef(jour_xyz):
    '''
    ppe: coefficient de conversion en cas de changement en cours d'année
    'foy'
    '''    
    nbJour = (jour_xyz==0) + jour_xyz
    return 360/nbJour

def _ppe_elig(rfr, ppe_coef, marpac, veuf, celdiv, nbptr, _P):
    '''
    eligibilité à la ppe, returns a bool
    'foy'
    '''
    P = _P.ir.ppe
    seuil = (veuf|celdiv)*(P.eligi1 + 2*max_(nbptr-1,0)*P.eligi3) \
            + marpac*(P.eligi2 + 2*max_(nbptr-2,0)*P.eligi3)
    out = (rfr*ppe_coef) <= seuil
    return out

def _ppe_rev(sal, hsup, rpns, _P):
    '''
    base ressource de la ppe
    'ind'
    '''
    P = _P.ir.ppe
    # Revenu d'activité salarié
    rev_sa = sal + hsup #+ TV + TW + TX + AQ + LZ + VJ
    # Revenu d'activité non salarié
    rev_ns = min_(0,rpns)/P.abatns + max_(0,rpns)*P.abatns
    return rev_sa + rev_ns

def _ppe_coeff_tp(ppeHeure, ppeJours, ppeCheckBox, ppe_tp_ns, _P):
    P = _P.ir.ppe
    frac_sa = ppeHeure/P.TP_nbh
    frac_ns = ppeJours/P.TP_nbj
    # TODO: changer ppeCheckBox en ppe_tp_sa
    tp = (ppeCheckBox == 1)|(ppe_tp_ns == 1)|(frac_sa + frac_ns >= 1)
    return tp + not_(tp)*(frac_sa + frac_ns) 
    
def _ppe_base(ppe_rev, ppe_coeff_tp, ppe_coef):
    out = ppe_rev/(ppe_coeff_tp + (ppe_coeff_tp==0))*ppe_coef
    return out

def _ppe_elig_i(ppe_rev, ppe_coef_tp, _P):
    '''
    eligibilité individuelle à la ppe
    '''
    P = _P.ir.ppe
    return (ppe_rev >= P.seuil1)&(_ppe_coeff_tp!=0)

def _ppe(ppe_elig, ppe_elig_i, ppe_rev, ppe_base, ppe_coef, ppe_coef_tp, nb_pac, marpac, celdiv, veuf, caseT, caseL, nbH, _P, _option = {'ppe_elig_i': ALL, 'ppe_base': ALL, 'ppe_rev': ALL, 'ppe_coef_tp': ALL}):
    '''
    Prime pour l'emploi
    '''
    P = _P.ir.ppe

    eliv, elic, eli1, eli2, eli3 = ppe_elig_i[VOUS], ppe_elig_i[CONJ], ppe_elig_i[PAC1], ppe_elig_i[PAC2], ppe_elig_i[PAC3], 
    basevi, baseci = ppe_rev[VOUS], ppe_rev[CONJ]
    basev, basec, base1, base2, base3  = ppe_base[VOUS], ppe_base[CONJ], ppe_base[PAC1], ppe_base[PAC2], ppe_base[PAC1]
    coef_tpv, coef_tpc, coef_tp1, coef_tp2, coef_tp3  = ppe_coef_tp[VOUS], ppe_coef_tp[CONJ], ppe_coef_tp[PAC1], ppe_coef_tp[PAC2], ppe_coef_tp[PAC1]
    
    nb_pac_ppe = max_(0, nb_pac - eli1 - eli2 -eli3 )
        
    ligne2 = marpac & xor_(basevi >= P.seuil1, baseci >= P.seuil1)
    ligne3 = (celdiv | veuf) & caseT & not_(veuf & caseT & caseL)
    ligne1 = not_(ligne2) & not_(ligne3)
    
    base_monact = ligne2*(eliv*basev + elic*basec)
    base_monacti = ligne2*(eliv*basevi + elic*baseci)

    def ppe_bar1(base):
        cond1 = ligne1 | ligne3
        cond2 = ligne2
        return 1/ppe_coef*((cond1 & (base <= P.seuil2))*(base)*P.taux1 +
                           (cond1 & (base> P.seuil2) & (base <= P.seuil3))*(P.seuil3 - base)*P.taux2 +
                           (cond2 & (base <= P.seuil2))*(base*P.taux1 ) +
                           (cond2 & (base >  P.seuil2) & (base <= P.seuil3))*((P.seuil3 - base)*P.taux2) +
                           (cond2 & (base >  P.seuil4) & (base <= P.seuil5))*(P.seuil5 - base)*P.taux3)

    def ppe_bar2(base):
        return 1/ppe_coef*((base <= P.seuil2)*(base)*P.taux1 +
                           ((base> P.seuil2) & (base <= P.seuil3))*(P.seuil3 - base1)*P.taux2 )

    # calcul des primes individuelles.
    ppev = eliv*ppe_bar1(basev)
    ppec = elic*ppe_bar1(basec)
    ppe1 = eli1*ppe_bar2(base1)
    ppe2 = eli2*ppe_bar2(base2)
    ppe3 = eli3*ppe_bar2(base3)
    
    ppe_monact_vous = (eliv & ligne2 & (basevi>=P.seuil1) & (basev <= P.seuil4))*P.monact
    ppe_monact_conj = (elic & ligne2 & (baseci>=P.seuil1) & (basec <= P.seuil4))*P.monact
    
    maj_pac = ppe_elig*(eliv|elic)*(
        (ligne1 & marpac & ((ppev+ppec)!=0) & (min_(basev,basec)<= P.seuil3))*P.pac*(nb_pac_ppe + nbH*0.5) +
        (ligne1 & (celdiv | veuf) & eliv & (basev<=P.seuil3))*P.pac*(nb_pac_ppe + nbH*0.5) +
        (ligne2 & (base_monacti >= P.seuil1) & (base_monact <= P.seuil3))*P.pac*(nb_pac_ppe + nbH*0.5) +
        (ligne2 & (base_monact > P.seuil3) & (base_monact <= P.seuil5))*P.pac*((nb_pac_ppe!=0) + 0.5*((nb_pac_ppe==0) & (nbH!=0))) +
        (ligne3 & (basevi >=P.seuil1) & (basev <= P.seuil3))*((min_(nb_pac_ppe,1)*2*P.pac + max_(nb_pac_ppe-1,0)*P.pac) + (nb_pac_ppe==0)*(min_(nbH,2)*P.pac + max_(nbH-2,0)*P.pac*0.5)) +
        (ligne3 & (basev  > P.seuil3) & (basev <= P.seuil5))*P.pac*((nb_pac_ppe!=0)*2 +((nb_pac_ppe==0) & (nbH!=0))))

    def coef(coef_tp):
        return (coef_tp <=0.5)*coef_tp*1.45 + (coef_tp > 0.5)*(0.55*coef_tp + 0.45)
    
    ppe_vous = ppe_elig*(ppev*coef(coef_tpv) + ppe_monact_vous)
    ppe_conj = ppe_elig*(ppec*coef(coef_tpc) + ppe_monact_conj)
    ppe_pac1 = ppe_elig*(ppe1*coef(coef_tp1))
    ppe_pac2 = ppe_elig*(ppe2*coef(coef_tp2))
    ppe_pac3 = ppe_elig*(ppe3*coef(coef_tp3))
    
    ppe_tot = ppe_vous + ppe_conj + ppe_pac1 + ppe_pac2 + ppe_pac3 +  maj_pac
    
    ppe_tot = (ppe_tot!=0)*max_(P.versmin,ppe_vous + ppe_conj + ppe_pac1 + ppe_pac2 + ppe_pac3 + maj_pac)
            
    return ppe_tot