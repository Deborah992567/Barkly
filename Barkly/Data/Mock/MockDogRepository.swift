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

    func updateDog(_ dog: Dog) async throws {
        await store.update(dog)
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

    func update(_ dog: Dog) {
        if let index = dogs.firstIndex(where: { $0.id == dog.id }) {
            dogs[index] = dog
        }
    }
}