# Audit Fix Retest

Un skill Codex pour auditer un projet, corriger les erreurs constatées, retester
les parcours et produire des rapports appuyés par des preuves.

Il fonctionne avec les outils du projet, sans imposer de langage, d’hébergement ou
de framework. Sites, API, applications mobiles ou de bureau, CLI, bibliothèques,
traitements de données et infrastructure : les contrôles suivent leurs contrats
réels. Les ressources indisponibles restent signalées comme non vérifiées.

## Ce que le skill apporte

- Un audit de sécurité et une recette fonctionnelle adaptés au périmètre demandé.
- Une boucle de reproduction, diagnostic, correction et retest, sans abaisser les
  règles du produit pour obtenir un résultat positif.
- Des vérifications des rôles, de l’isolation, des transitions, de la persistance,
  des sorties produites et des reprises après erreur quand elles s’appliquent.
- La distinction entre code commité, code poussé, CI réussie, déploiement et
  comportement effectivement vérifié sur la version publiée.
- Deux rapports détaillés, Word et PDF par défaut, avec captures réelles ou autres
  preuves pertinentes. Les limites et les risques restants sont visibles.

Les instructions principales sont en anglais pour faciliter le partage. Le skill
répond et produit ses rapports dans la langue de la demande.

## Installation dans Codex

Copier le dossier complet `audit-fix-retest` dans `~/.codex/skills/`, ou dans le
sous-dossier `skills/` de votre `CODEX_HOME` personnalisé. Pour un dépôt qui contient
directement ce dossier à sa racine, le cloner sous ce nom à cet emplacement :

```bash
git clone <URL_DE_VOTRE_DEPOT> ~/.codex/skills/audit-fix-retest
```

Utiliser ensuite `$audit-fix-retest` dans une conversation ayant accès au projet.
La sélection automatique reste activée par défaut pour les demandes d’audit et de
recette ; un changement de code ordinaire ne justifie pas une campagne complète.

## Exemple de demande

```text
Utilise $audit-fix-retest pour auditer ce projet avant livraison.
Teste les parcours critiques, les droits et les reprises après erreur.
Corrige les anomalies et reteste les mêmes scénarios.
Produis un audit de sécurité et un audit de livraison en Word et PDF,
avec captures et résultats détaillés. Signale les points non vérifiés.
```

Le skill utilise les autorisations déjà données. Il ne fournit pas d’accès à vos
comptes, n’autorise pas un paiement ou un message réel et ne publie pas un dépôt
de lui-même. Fournir les identifiants via un fichier privé ou un gestionnaire de
secrets disponible ; ne pas les inscrire dans le skill ou ses exemples.

## Prérequis et outils facultatifs

Les instructions ne dépendent d’aucun connecteur particulier. Codex doit avoir
accès au projet et aux outils nécessaires aux contrôles choisis. L’application
testée conserve ses propres dépendances et moyens de recette.

Le script facultatif `scripts/audit_ledger.py` utilise Python 3.10 ou supérieur,
sans dépendance externe. Il vérifie un registre local, conserve les tentatives,
calcule les empreintes des preuves et produit deux sources Markdown. Il n’exécute
pas les tests, ne réalise aucun appel réseau et ne génère pas Word/PDF à lui seul.
Son format est décrit dans [references/ledger.md](references/ledger.md).

La production finale Word/PDF nécessite des outils de création, conversion et
rendu disponibles dans l’environnement. Les skills Documents et PDF peuvent être
utilisés lorsqu’ils sont installés. Une impossibilité de conversion ou de contrôle
visuel doit être signalée, sans prétendre livrer un format qui n’a pas été produit.

## Vérification du paquet

```bash
python3 -m unittest discover -s tests -v
python3 scripts/audit_ledger.py --help
```

Les tests couvrent notamment les faux résultats positifs, les preuves modifiées,
les chemins hors du dossier, les retests et les déclarations de préparation à la
production sans couverture suffisante. La CI du dépôt exécute ces tests sans
accès à un service externe.

## Publication sur GitHub

Le dossier est autonome et peut devenir la racine d’un dépôt public. Publier les
instructions, références, scripts et tests ; conserver les registres, captures,
rapports et secrets des projets audités hors de ce dépôt. Le `.gitignore` constitue
une aide, pas un contrôle automatique de confidentialité.

Ce paquet ne contient aucune donnée du projet dont la méthode est issue. Un audit
reste limité au périmètre et aux preuves réellement exercés ; le skill ne délivre
pas de certification automatique de sécurité ou de production.

Licence MIT, voir [LICENSE](LICENSE).
