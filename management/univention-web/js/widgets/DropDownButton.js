/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2020-2024 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dijit/form/DropDownButton",
	"./Icon",
	"put-selector/put"
], function(declare, domClass, domConstruct, DropDownButton, Icon, put) {
	return declare("umc.widgets.DropDownButton", [ DropDownButton ], {
		//// overwrites
		iconClass: 'more-horizontal',
		_setIconClassAttr: function(iconClass) {
			if (iconClass) {
				if (this.iconNode) {
					Icon.setIconOfNode(this.iconNode, iconClass);
				} else {
					this.iconNode = Icon.createNode(iconClass);
					domConstruct.place(this.iconNode, this.titleNode, 'first');
				}
			} else {
				if (this.iconNode) {
					this.iconNode.remove();
					this.iconNode = null;
				}
			}
			this._set('iconClass', iconClass);
		},


		//// lifecycle
		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'ucsButton');
			put(this.iconNode, '!');
			this.iconNode = null;
		}
	});
});
