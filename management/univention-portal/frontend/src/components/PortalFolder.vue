<!--
  Copyright 2021-2024 Univention GmbH

  https://www.univention.de/

  All rights reserved.

  The source code of this program is made available
  under the terms of the GNU Affero General Public License version 3
  (GNU AGPL V3) as published by the Free Software Foundation.

  Binary versions of this program provided by Univention to you as
  well as other copyrighted, protected or trademarked materials like
  Logos, graphics, fonts, specific documentations and configurations,
  cryptographic keys etc. are subject to a license agreement between
  you and Univention and not subject to the GNU AGPL V3.

  In the case you use this program under the terms of the GNU AGPL V3,
  the program is provided in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License with the Debian GNU/Linux or Univention distribution in file
  /usr/share/common-licenses/AGPL-3; if not, see
  <https://www.gnu.org/licenses/>.
-->
<template>
  <div
    class="portal-folder"
    :draggable="editMode && !inModal"
    :class="[
      { 'portal-folder__in-modal': inModal },
    ]"
    @dragstart="dragstart"
    @dragenter="dragenter"
    @dragend="dragend"
    @dragover.prevent
    @drop="dropped"
  >
    <tabindex-element
      :id="id"
      :tag="isOpened"
      :active-at="activeAt"
      class="portal-tile__box"
      :class="[{
        'portal-tile__box--accessible-zoom': inModal && updateZoomQuery(),
        'portal-tile__box--dragging': isBeingDragged,
        'portal-tile__box--with-scaling-hover': !inModal,
      }]"
      :aria-label="ariaLabelFolder"
      @click="openFolder"
      @keypress.enter="openFolder"
      @keydown.esc.stop="closeFolder"
    >
      <region
        :id="`${id}-content`"
        :aria-role="ariaRole"
        class="portal-folder__thumbnails"
        tabindex="-1"
        role="none"
        :class="{ 'portal-folder__thumbnails--in-modal': inModal }"
      >
        <div
          v-for="(tile, index) in filteredTiles"
          :key="tile.id"
          :class="`portal-folder__thumbnail ${isMoreThanFiveOrTen(index)}`"
        >
          <portal-tile
            :id="`${inModal ? 'modal-' : 'folder-'}${tile.id}`"
            :ref="'portalFolderChildren' + index"
            :layout-id="tile.layoutId"
            :dn="tile.dn"
            :super-dn="dn"
            :title="tile.title"
            :description="tile.description"
            :keywords="tile.keywords"
            :activated="tile.activated"
            :anonymous="tile.anonymous"
            :background-color="tile.backgroundColor"
            :links="tile.links"
            :allowed-groups="tile.allowedGroups"
            :link-target="tile.linkTarget"
            :target="tile.target"
            :original-link-target="tile.originalLinkTarget"
            :path-to-logo="tile.pathToLogo"
            :minified="!inModal"
            :from-folder="true"
          />
        </div>
        <div
          v-if="editMode && inModal"
          class="portal-folder__thumbnail portal-folder__thumbnail--tile-add"
        >
          <div class="portal-tile__root-element">
            <tile-add
              :for-folder="true"
              :super-dn="dn"
              :super-layout-id="layoutId"
            />
          </div>
        </div>
      </region>
    </tabindex-element>
    <span
      class="portal-folder__name"
      @click="openFolder"
    >
      {{ $localized(title) }}
    </span>
    <div class="portal-tile__icon-bar">
      <icon-button
        v-if="editMode && !inModal && showEditButtonWhileDragging"
        icon="edit-2"
        class="button--icon--circle button--icon--edit-mode button--shadow"
        :aria-label-prop="EDIT_FOLDER"
        @click="editFolder"
      />
      <icon-button
        v-if="editMode && !inModal && showMoveButtonWhileDragging"
        :id="`${layoutId}-move-button`"
        ref="mover"
        icon="move"
        class="button--icon--circle button--icon--edit-mode button--shadow"
        :aria-label-prop="MOVE_FOLDER"
        @click="dragKeyboardClick"
        @keydown.esc="dragend"
        @keydown.left="dragKeyboardDirection($event, 'left')"
        @keydown.right="dragKeyboardDirection($event, 'right')"
        @keydown.up="dragKeyboardDirection($event, 'up')"
        @keydown.down="dragKeyboardDirection($event, 'down')"
        @keydown.tab="handleTabWhileMoving"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

import Region from '@/components/activity/Region.vue';
import TabindexElement from '@/components/activity/TabindexElement.vue';
import PortalTile from '@/components/PortalTile.vue';
import Draggable from '@/mixins/Draggable.vue';
import IconButton from '@/components/globals/IconButton.vue';
import TileAdd from '@/components/admin/TileAdd.vue';
import { LocalizedString, Tile, TileOrFolder } from '@/store/modules/portalData/portalData.models';
import _ from '@/jsHelper/translate';
import { doesTitleMatch, doesKeywordsMatch, doesDescriptionMatch } from '@/jsHelper/portalCategories';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'PortalFolder',
  components: {
    PortalTile,
    IconButton,
    TileAdd,
    TabindexElement,
    Region,
  },
  mixins: [
    Draggable,
  ],
  props: {
    id: {
      type: String,
      default: '',
    },
    layoutId: {
      type: String,
      required: true,
    },
    dn: {
      type: String,
      required: true,
    },
    superDn: {
      type: String,
      required: true,
    },
    title: {
      type: Object as PropType<LocalizedString>,
      required: true,
    },
    tiles: {
      type: Array as PropType<Tile[]>,
      required: true,
    },
    inModal: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    ...mapGetters({
      lastDir: 'dragndrop/getLastDir',
      searchQuery: 'search/searchQuery',
    }),
    activeAt(): string[] {
      if (this.editMode) {
        return ['portal'];
      }
      return ['portal', 'header-search'];
    },
    ariaLabelFolder(): string | null {
      const numberOfItems = this.tiles.length;
      let itemString = '';
      if (this.tiles.length === 0) {
        itemString = _('No items');
      } else if (this.tiles.length === 1) {
        itemString = _('Item');
      } else {
        itemString = _('Items');
      }

      return !this.inModal ? `${this.$localized(this.title)} ${_('Folder')}: ${numberOfItems} ${itemString}` : null;
    },
    isOpened(): string {
      return this.inModal ? 'div' : 'button';
    },
    EDIT_FOLDER(): string {
      return _('Edit Folder: %(folder)s', { folder: this.$localized(this.title) });
    },
    MOVE_FOLDER(): string {
      return _('Move Folder: %(folder)s', { folder: this.$localized(this.title) });
    },
    filteredTiles(): Tile[] {
      const filteredTiles = this.tiles.filter((tile) => (
        doesTitleMatch(tile as TileOrFolder, this.searchQuery) ||
        doesDescriptionMatch(tile as TileOrFolder, this.searchQuery) ||
        doesKeywordsMatch(tile as TileOrFolder, this.searchQuery)
      ));
      if (filteredTiles.length === 0) {
        return this.tiles;
      }
      return filteredTiles;
    },
    ariaRole(): string {
      if (this.inModal && this.editMode) {
        return 'application';
      }
      return this.inModal ? 'region' : 'none';
    },
  },
  mounted() {
    this.$nextTick(() => {
      window.addEventListener('resize', this.updateZoomQuery);
    });

    if (this.$refs.mover) {
      // @ts-ignore
      this.handleDragFocus(this.$refs.mover.$el, this.lastDir);
    }
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.updateZoomQuery);
  },
  methods: {
    async dropped() {
      if (!this.editMode || !this.inModal) {
        return;
      }
      this.$store.dispatch('portalData/saveLayout');
    },
    closeFolder(): void {
      this.$store.dispatch('modal/closeFolder');
    },
    openFolder(ev: Event) {
      if (this.inModal) {
        return;
      }
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'PortalFolder',
        props: { ...this.$props, id: `${this.id}-modal`, inModal: true },
      });
      this.$store.dispatch('activity/setRegion', `${this.id}-modal-content`);
      ev.stopPropagation();
    },
    editFolder() {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'AdminFolder',
        stubborn: true,
        props: {
          modelValue: this.$props,
          superDn: this.superDn,
          label: _('Edit folder'),
        },
      });
    },
    isMoreThanFiveOrTen(index): string {
      let classSuffix = '';
      if (!this.inModal) {
        if (index === 3 && this.tiles.length > 4) {
          classSuffix = 'portal-folder__thumbnail--mobile';
        } else if (index === 8 && this.tiles.length >= 10) {
          classSuffix = 'portal-folder__thumbnail--desktop';
        }
      }
      return classSuffix;
    },
    updateZoomQuery(): boolean {
      const browserZoomLevel = Math.round((window.devicePixelRatio * 100) / 2);
      // BROWSER ZOOM DEFAULT: 100
      // MOBILE ZOOM DEFAULT: 100 - 150
      // BROWSER ZOOM WCAG2.1 AA: 200
      return !!browserZoomLevel && browserZoomLevel >= 200;
    },
  },
});
</script>

<style lang="stylus">
.portal-folder
  position: relative
  width: var(--app-tile-side-length)
  display: flex
  flex-direction: column
  align-items: center
  cursor: pointer

  &__name
    font-weight: var(--font-weight-bold)
    text-align: center
    width: 100%
    word-wrap: break-word
    hyphens: auto

  &__in-modal
    cursor: default
    width: calc(3*var(--app-tile-side-length))
    max-width: @width

    .portal-tile__root-element
      align-items: flex-start!important;

    button
      text-transform: none

    .portal-folder__name
      font-size: var(--font-size-1)
      width: 100%

    > .portal-tile

      &__box // Big FOLDER
        width: calc(5 * var(--app-tile-side-length))
        height: @width
        max-width: 100vw
        margin-bottom: calc(2 * var(--layout-spacing-unit))
        max-height: 80vh
        border-radius: 2rem

        @media $mqSmartphone
          max-width: 90vw
          margin-bottom: 0
          max-height: 90vw
          border-radius: 2rem

        &--accessible-zoom
          @media $mqSmartphone
            max-height: calc(100vh -  var(--portal-header-height) - (10 * var(--layout-spacing-unit)));
            margin-top: calc(var(--portal-header-height) + var(--layout-spacing-unit));

        .portal-tile
          width: var(--app-tile-side-length)

          &__box
            width: var(--app-tile-side-length)
            height: @width
            margin-bottom: calc(2 * var(--layout-spacing-unit))
    .portal-folder__thumbnail
      margin-bottom: calc(5 * var(--layout-spacing-unit))

    .portal-folder__thumbnails .portal-tile__name
        display: block;

  &__thumbnails
    width: 100%
    height: 100%
    display: flex
    flex-wrap: wrap;
    justify-content: flex-start;
    align-content: flex-start;
    padding: 0.3rem;
    box-sizing: border-box;
    overflow: hidden
    outline: 0
    > div
        display: flex
        align-content: center
        justify-content: center

    &--in-modal
      max-height: calc(100vh - var(--portal-header-height) - var(--portal-header-height) - var(--portal-header-height));
      overflow: auto
      box-sizing: border-box;
      padding:  var(--portal-folder-padding)
      padding-bottom: 0

      > div
        height: auto
      .portal-folder__thumbnail--tile-add
        align-items: start
      .portal-folder__thumbnail:after {
        display: none;
      }
      .portal-folder__thumbnail:nth-child(n+10)
        display: block
    .portal-tile--minified:focus .portal-tile__box
      border-color: transparent

    .portal-tile
      width: calc(0.25 * var(--app-tile-side-length))

      &__box
        width: calc(0.25 * var(--app-tile-side-length))
        height: @width
        padding:  calc(var(--layout-spacing-unit))
        margin-bottom: 0

      &__name
        display: none
      &__root-element
        align-items: center
      ^[0]__thumbnail
        margin-bottom: 0
        display: flex
        align-content: center
        justify-content: center
        width: var(--portal-folder-tile-width)
        height: var(--portal-folder-tile-width)

        @media $mqSmartphone
          height: 50%
          width: var(--portal-folder-tile-width)
          max-width: 50%

  .portal-tile__box
    background-color: var(--bgc-content-container)
    padding: 0
    overflow: hidden

    .portal-tile__box
      background-color: var(--bgc-apptile-default)

  &__thumbnail
    &:nth-child(n+10)
      display: none
    &--desktop
      position: relative

      .portal-tile__box
        box-shadow: none

      &:after
          content: '...'
          position: absolute
          width: 100%
          height: @width
          top: 0
          bottom:0
          right: 0
          line-height: 300%
          background-color: var(--bgc-content-container)
        @media $mqSmartphone
          display: none

    &--mobile
      position: relative

      &:after
        @media $mqSmartphone
          content: '...'
          position: absolute
          width: 100%
          height: @width
          top: 0
          bottom:0
          right: 0
          line-height: 300%
          background-color: var(--bgc-content-container)

</style>
