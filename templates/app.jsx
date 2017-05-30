class Users extends React.Component {
    render() {
        return <<UserTable data=/>
    }
}

class Category extends React.Component {
    render() {
        return <h2>Категории</h2>
    }
}

class Product extends React.Component {
    render() {
        return <h2>Товары</h2>
    }
}

class Orders extends React.Component {
    render() {
        return <h2>Товары в корзине</h2>
    }
}

class NotFound extends React.Component {
    render() {
        return <h2>Ресурс не найден</h2>;
    }
}