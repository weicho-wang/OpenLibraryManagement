Component({
    properties: {
        book: {
            type: Object,
            value: {}
        }
    },

    methods: {
        onTap() {
            this.triggerEvent('tapcard', { isbn: this.properties.book.isbn });
        }
    }
});
