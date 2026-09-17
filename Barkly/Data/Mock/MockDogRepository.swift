import Foundation

final class MockDogRepository: DogRepository {
    private let store: InMemoryDogStore

    init(seedDogs: [Dog] = MockSeeds.demoDogs) {
        store = InMemoryDogStore(dogs: seedDogs)
    }

    func fetchDogs() async throws -> [Dog] {
        await store.load()
    }

    func fetchDog(id: UUID) async throws -> Dog? {
        await store.load().first { $0.id == id }
    }

    func updateDog(_ dog: Dog) async throws -> Dog {
        await store.update(dog)
        return dog
    }

    func createDog(name: String, breed: String?, dateOfBirth: Date, notes: String?) async throws -> Dog {
        let dog = Dog(name: name, breed: breed ?? "", dateOfBirth: dateOfBirth, notes: notes)
        await store.add(dog)
        return dog
    }
}

actor InMemoryDogStore {
    private var dogs: [Dog]

    init(dogs: [Dog]) {
        self.dogs = dogs
    }

    func load() -> [Dog] {
        dogs
    }

    func add(_ dog: Dog) {
        dogs.append(dog)
    }

    func update(_ dog: Dog) {
        if let index = dogs.firstIndex(where: { $0.id == dog.id }) {
            dogs[index] = dog
        }
    }
}